import os
import json
import uuid
import time
import threading
from datetime import datetime
import redis
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Configuration
CARS_SERVICE_URL = os.getenv('CARS_SERVICE_URL', 'http://cars-service:8070')
RENTAL_SERVICE_URL = os.getenv('RENTAL_SERVICE_URL', 'http://rental-service:8060')
PAYMENT_SERVICE_URL = os.getenv('PAYMENT_SERVICE_URL', 'http://payment-service:8050')
REDIS_URL = os.getenv('REDIS_URL', 'redis://redis:6379')

# Circuit Breaker configuration
CIRCUIT_FAILURE_THRESHOLD = 3
CIRCUIT_RECOVERY_TIMEOUT = 30

# Redis client
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

# Statistics for circuit breakers
circuit_stats = {
    'cars': {'failures': 0, 'last_failure': None, 'state': 'CLOSED'},
    'rental': {'failures': 0, 'last_failure': None, 'state': 'CLOSED'},
    'payment': {'failures': 0, 'last_failure': None, 'state': 'CLOSED'}
}

def is_service_error(exception):
    """Check if exception is due to service unavailability"""
    return isinstance(exception, (
        requests.exceptions.ConnectionError,
        requests.exceptions.Timeout,
        requests.exceptions.HTTPError
    ))

def update_circuit_stats(service, success):
    """Update circuit breaker statistics"""
    if success:
        circuit_stats[service]['failures'] = 0
        circuit_stats[service]['state'] = 'CLOSED'
    else:
        circuit_stats[service]['failures'] += 1
        circuit_stats[service]['last_failure'] = time.time()
        if circuit_stats[service]['failures'] >= CIRCUIT_FAILURE_THRESHOLD:
            circuit_stats[service]['state'] = 'OPEN'
            # Schedule recovery check
            threading.Timer(CIRCUIT_RECOVERY_TIMEOUT, check_service_recovery, [service]).start()

def check_service_recovery(service):
    """Check if service has recovered"""
    try:
        if service == 'cars':
            response = requests.get(f'{CARS_SERVICE_URL}/manage/health', timeout=2)
        elif service == 'rental':
            response = requests.get(f'{RENTAL_SERVICE_URL}/manage/health', timeout=2)
        elif service == 'payment':
            response = requests.get(f'{PAYMENT_SERVICE_URL}/manage/health', timeout=2)
        
        if response.status_code == 200:
            circuit_stats[service]['state'] = 'CLOSED'
            circuit_stats[service]['failures'] = 0
            print(f"Service {service} recovered!")
        else:
            # Schedule another check
            threading.Timer(CIRCUIT_RECOVERY_TIMEOUT, check_service_recovery, [service]).start()
    except:
        # Schedule another check
        threading.Timer(CIRCUIT_RECOVERY_TIMEOUT, check_service_recovery, [service]).start()

def circuit_breaker(service):
    """Circuit breaker decorator"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            if circuit_stats[service]['state'] == 'OPEN':
                # Return fallback response
                print(f"Circuit breaker OPEN for {service}, returning fallback")
                return get_fallback_response(service, *args, **kwargs)
            
            try:
                result = func(*args, **kwargs)
                update_circuit_stats(service, True)
                return result
            except Exception as e:
                if is_service_error(e):
                    update_circuit_stats(service, False)
                    print(f"Service {service} error: {e}")
                    # Return fallback response after updating stats
                    return get_fallback_response(service, *args, **kwargs)
                else:
                    # Re-raise non-service errors
                    raise e
        # Сохраняем оригинальное имя функции для Flask endpoint
        wrapper.__name__ = func.__name__ + f'_{service}'
        return wrapper
    return decorator

def get_fallback_response(service, *args, **kwargs):
    """Return fallback responses for different services"""
    if service == 'cars':
        # Return empty array for cars in expected format
        return jsonify({
            'page': 1,
            'pageSize': 0,
            'totalElements': 0,
            'items': []
        }), 200
    elif service == 'rental':
        # Return empty array for rentals
        return jsonify([]), 200
    elif service == 'payment':
        # For payment operations, we can't provide fallback
        return jsonify({'error': 'Payment service unavailable'}), 503

def add_to_retry_queue(operation, data):
    """Add operation to retry queue"""
    retry_id = str(uuid.uuid4())
    queue_item = {
        'id': retry_id,
        'operation': operation,
        'data': data,
        'created_at': datetime.now().isoformat(),
        'retry_count': 0
    }
    redis_client.rpush('retry_queue', json.dumps(queue_item))
    return retry_id

def process_retry_queue():
    """Background thread to process retry queue"""
    while True:
        try:
            queue_item_json = redis_client.lpop('retry_queue')
            if queue_item_json:
                queue_item = json.loads(queue_item_json)
                queue_item['retry_count'] += 1
                
                try:
                    if queue_item['operation'] == 'create_rental':
                        # Retry rental creation
                        success = retry_create_rental(queue_item['data'])
                        if not success and queue_item['retry_count'] < 5:
                            # Re-add to queue for another try
                            redis_client.rpush('retry_queue', json.dumps(queue_item))
                    
                    elif queue_item['operation'] == 'cancel_rental':
                        # Retry rental cancellation
                        success = retry_cancel_rental(queue_item['data'])
                        if not success and queue_item['retry_count'] < 5:
                            redis_client.rpush('retry_queue', json.dumps(queue_item))
                
                except Exception as e:
                    print(f"Error processing retry queue: {e}")
                    if queue_item['retry_count'] < 5:
                        redis_client.rpush('retry_queue', json.dumps(queue_item))
        
        except Exception as e:
            print(f"Error in retry queue processor: {e}")
        
        time.sleep(10)  # Check every 10 seconds

def retry_create_rental(data):
    """Retry rental creation operation"""
    try:
        # Get car info
        car_response = requests.get(f'{CARS_SERVICE_URL}/api/v1/cars/{data["car_uid"]}', timeout=5)
        if car_response.status_code != 200:
            return False
        
        # Reserve car
        reserve_response = requests.patch(
            f'{CARS_SERVICE_URL}/api/v1/cars/{data["car_uid"]}/availability', 
            json={'availability': False},
            timeout=5
        )
        if reserve_response.status_code != 200:
            return False
        
        # Create rental
        rental_data = {
            'carUid': data['car_uid'],
            'dateFrom': data['date_from'],
            'dateTo': data['date_to'],
            'paymentUid': data['payment_uid'],
            'status': 'IN_PROGRESS'
        }
        
        rental_response = requests.post(
            f'{RENTAL_SERVICE_URL}/api/v1/rental', 
            headers={'X-User-Name': data['username'], 'Content-Type': 'application/json'},
            json=rental_data,
            timeout=5
        )
        
        return rental_response.status_code == 201
        
    except:
        return False

def retry_cancel_rental(data):
    """Retry rental cancellation operation"""
    try:
        # Free car
        requests.patch(
            f'{CARS_SERVICE_URL}/api/v1/cars/{data["car_uid"]}/availability', 
            json={'availability': True},
            timeout=5
        )
        
        # Cancel payment
        requests.patch(
            f'{PAYMENT_SERVICE_URL}/api/v1/payments/{data["payment_uid"]}',
            timeout=5
        )
        
        # Update rental status
        cancel_response = requests.delete(
            f'{RENTAL_SERVICE_URL}/api/v1/rental/{data["rental_uid"]}',
            headers={'X-User-Name': data['username']},
            timeout=5
        )
        
        return cancel_response.status_code == 204
        
    except:
        return False

@app.route('/manage/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'OK'}), 200

# Cars Service endpoints with Circuit Breaker
@app.route('/api/v1/cars', methods=['GET'])
@circuit_breaker('cars')
def get_cars():
    response = requests.get(f'{CARS_SERVICE_URL}/api/v1/cars', params=request.args, timeout=2)
    response.raise_for_status()
    return jsonify(response.json()), response.status_code

# Rental Service endpoints with Circuit Breaker
@app.route('/api/v1/rental', methods=['GET'])
@circuit_breaker('rental')
def get_rentals():
    headers = {'X-User-Name': request.headers.get('X-User-Name', '')}
    response = requests.get(f'{RENTAL_SERVICE_URL}/api/v1/rental', headers=headers, timeout=2)
    response.raise_for_status()
    
    # Enhance response with car and payment details
    rentals = response.json()
    enhanced_rentals = []
    
    for rental in rentals:
        try:
            # Get car details
            car_response = requests.get(f'{CARS_SERVICE_URL}/api/v1/cars/{rental["carUid"]}', timeout=2)
            car_info = car_response.json() if car_response.status_code == 200 else {
                'carUid': rental['carUid'],
                'brand': 'Unknown',
                'model': 'Unknown', 
                'registrationNumber': 'Unknown'
            }
            
            # Get payment details
            payment_response = requests.get(f'{PAYMENT_SERVICE_URL}/api/v1/payments/{rental["paymentUid"]}', timeout=2)
            payment_info = payment_response.json() if payment_response.status_code == 200 else {
                'paymentUid': rental['paymentUid'],
                'status': 'UNKNOWN',
                'price': 0
            }
            
            enhanced_rentals.append({
                'rentalUid': rental['rentalUid'],
                'status': rental['status'],
                'dateFrom': rental['dateFrom'],
                'dateTo': rental['dateTo'],
                'car': {
                    'carUid': car_info['carUid'],
                    'brand': car_info['brand'],
                    'model': car_info['model'],
                    'registrationNumber': car_info['registrationNumber']
                },
                'payment': payment_info
            })
        except:
            # If any service fails, return basic rental info
            enhanced_rentals.append({
                'rentalUid': rental['rentalUid'],
                'status': rental['status'],
                'dateFrom': rental['dateFrom'],
                'dateTo': rental['dateTo'],
                'carUid': rental['carUid'],
                'paymentUid': rental['paymentUid']
            })
    
    return jsonify(enhanced_rentals), 200

@app.route('/api/v1/rental/<rental_uid>', methods=['GET'])
def get_rental(rental_uid):
    """Get specific rental by UUID"""
    try:
        username = request.headers.get('X-User-Name')
        if not username:
            return jsonify({'error': 'X-User-Name header is required'}), 400
        
        # Get rental info from rental service
        try:
            rental_response = requests.get(
                f'{RENTAL_SERVICE_URL}/api/v1/rental/{rental_uid}',
                headers={'X-User-Name': username},
                timeout=2
            )
            if rental_response.status_code != 200:
                return jsonify({'error': 'Rental not found'}), 404
            rental_info = rental_response.json()
        except requests.exceptions.RequestException:
            return jsonify({'error': 'Rental service unavailable'}), 503
        
        # Get car details
        try:
            car_response = requests.get(
                f'{CARS_SERVICE_URL}/api/v1/cars/{rental_info["carUid"]}',
                timeout=2
            )
            if car_response.status_code == 200:
                car_info = car_response.json()
                car_details = {
                    'carUid': car_info['carUid'],
                    'brand': car_info['brand'],
                    'model': car_info['model'],
                    'registrationNumber': car_info['registrationNumber']
                }
            else:
                car_details = {
                    'carUid': rental_info['carUid'],
                    'brand': 'Unknown',
                    'model': 'Unknown',
                    'registrationNumber': 'Unknown'
                }
        except requests.exceptions.RequestException:
            car_details = {
                'carUid': rental_info['carUid'],
                'brand': 'Unknown',
                'model': 'Unknown',
                'registrationNumber': 'Unknown'
            }
        
        # Get payment details
        try:
            payment_response = requests.get(
                f'{PAYMENT_SERVICE_URL}/api/v1/payments/{rental_info["paymentUid"]}',
                timeout=2
            )
            if payment_response.status_code == 200:
                payment_info = payment_response.json()
            else:
                payment_info = {
                    'paymentUid': rental_info['paymentUid'],
                    'status': 'UNKNOWN',
                    'price': 0
                }
        except requests.exceptions.RequestException:
            payment_info = {
                'paymentUid': rental_info['paymentUid'],
                'status': 'UNKNOWN',
                'price': 0
            }
        
        # Build enhanced response
        enhanced_rental = {
            'rentalUid': rental_info['rentalUid'],
            'status': rental_info['status'],
            'dateFrom': rental_info['dateFrom'],
            'dateTo': rental_info['dateTo'],
            'car': car_details,
            'payment': payment_info
        }
        
        return jsonify(enhanced_rental), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/rental', methods=['POST'])
def create_rental():
    """Create rental with distributed transaction and retry queue"""
    try:
        username = request.headers.get('X-User-Name')
        if not username:
            return jsonify({'error': 'X-User-Name header is required'}), 400
        
        data = request.get_json()
        car_uid = data.get('carUid')
        date_from = data.get('dateFrom')
        date_to = data.get('dateTo')
        
        if not all([car_uid, date_from, date_to]):
            return jsonify({'error': 'carUid, dateFrom, and dateTo are required'}), 400
        
        # Step 1: Get car info
        try:
            car_response = requests.get(f'{CARS_SERVICE_URL}/api/v1/cars/{car_uid}', timeout=2)
            if car_response.status_code != 200:
                return jsonify({'error': 'Car not found'}), 404
            car_info = car_response.json()
        except requests.exceptions.RequestException:
            return jsonify({'error': 'Cars service unavailable'}), 503
        
        if not car_info['available']:
            return jsonify({'error': 'Car is not available'}), 400
        
        # Step 2: Calculate price
        days = (datetime.fromisoformat(date_to) - datetime.fromisoformat(date_from)).days
        if days <= 0:
            return jsonify({'error': 'Invalid date range'}), 400
        
        total_price = days * car_info['price']
        
        # Step 3: Create payment
        try:
            payment_response = requests.post(
                f'{PAYMENT_SERVICE_URL}/api/v1/payments', 
                json={'price': total_price},
                timeout=2
            )
            if payment_response.status_code != 201:
                return jsonify({'error': 'Payment creation failed'}), 500
            payment_info = payment_response.json()
        except requests.exceptions.RequestException as e:
            return jsonify({'message': 'Payment Service unavailable'}), 503
        
        # Step 4: Reserve car
        try:
            reserve_response = requests.patch(
                f'{CARS_SERVICE_URL}/api/v1/cars/{car_uid}/availability', 
                json={'availability': False},
                timeout=2
            )
            if reserve_response.status_code != 200:
                # Rollback payment
                try:
                    requests.patch(f'{PAYMENT_SERVICE_URL}/api/v1/payments/{payment_info["paymentUid"]}', timeout=1)
                except:
                    pass
                return jsonify({'error': 'Failed to reserve car'}), 500
        except requests.exceptions.RequestException:
            # Rollback payment
            try:
                requests.patch(f'{PAYMENT_SERVICE_URL}/api/v1/payments/{payment_info["paymentUid"]}', timeout=1)
            except:
                pass
            return jsonify({'error': 'Cars service unavailable'}), 503
        
        # Step 5: Create rental
        try:
            rental_data = {
                'carUid': car_uid,
                'dateFrom': date_from,
                'dateTo': date_to,
                'paymentUid': payment_info['paymentUid'],
                'status': 'IN_PROGRESS'
            }
            
            rental_response = requests.post(
                f'{RENTAL_SERVICE_URL}/api/v1/rental', 
                headers={'X-User-Name': username, 'Content-Type': 'application/json'},
                json=rental_data,
                timeout=2
            )
            
            if rental_response.status_code == 201:
                rental_info = rental_response.json()
                
                # Enhanced response with car and payment details
                return jsonify({
                    'rentalUid': rental_info['rentalUid'],
                    'status': rental_info['status'],
                    'dateFrom': rental_info['dateFrom'],
                    'dateTo': rental_info['dateTo'],
                    'car': {
                        'carUid': car_info['carUid'],
                        'brand': car_info['brand'],
                        'model': car_info['model'],
                        'registrationNumber': car_info['registrationNumber']
                    },
                    'payment': payment_info
                }), 200
            else:
                # Rollback everything
                try:
                    requests.patch(f'{CARS_SERVICE_URL}/api/v1/cars/{car_uid}/availability', 
                                  json={'availability': True}, timeout=1)
                    requests.patch(f'{PAYMENT_SERVICE_URL}/api/v1/payments/{payment_info["paymentUid"]}', timeout=1)
                except:
                    pass
                return jsonify({'error': 'Rental creation failed'}), 500
                
        except requests.exceptions.RequestException:
            # Rollback everything and add to retry queue
            try:
                requests.patch(f'{CARS_SERVICE_URL}/api/v1/cars/{car_uid}/availability', 
                              json={'availability': True}, timeout=1)
                requests.patch(f'{PAYMENT_SERVICE_URL}/api/v1/payments/{payment_info["paymentUid"]}', timeout=1)
            except:
                pass
            
            # Add to retry queue
            retry_data = {
                'username': username,
                'car_uid': car_uid,
                'date_from': date_from,
                'date_to': date_to,
                'payment_uid': payment_info['paymentUid'],
                'car_info': car_info,
                'total_price': total_price
            }
            add_to_retry_queue('create_rental', retry_data)
            
            # Return success to user despite background failure
            return jsonify({
                'message': 'Rental processing started',
                'status': 'PENDING'
            }), 202
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/rental/<rental_uid>/finish', methods=['POST'])
def finish_rental(rental_uid):
    """Finish rental with error handling"""
    try:
        username = request.headers.get('X-User-Name')
        if not username:
            return jsonify({'error': 'X-User-Name header is required'}), 400
        
        # Get rental info first
        try:
            rental_response = requests.get(
                f'{RENTAL_SERVICE_URL}/api/v1/rental/{rental_uid}',
                headers={'X-User-Name': username},
                timeout=2
            )
            if rental_response.status_code != 200:
                return jsonify({'error': 'Rental not found'}), 404
            rental_info = rental_response.json()
        except requests.exceptions.RequestException:
            return jsonify({'error': 'Rental service unavailable'}), 503
        
        car_uid = rental_info['carUid']
        
        # Update car availability
        try:
            requests.patch(
                f'{CARS_SERVICE_URL}/api/v1/cars/{car_uid}/availability', 
                json={'availability': True},
                timeout=1
            )
        except:
            # Non-critical failure, continue
            pass
        
        # Update rental status
        try:
            finish_response = requests.post(
                f'{RENTAL_SERVICE_URL}/api/v1/rental/{rental_uid}/finish',
                headers={'X-User-Name': username},
                timeout=2
            )
            return '', finish_response.status_code
        except requests.exceptions.RequestException:
            return jsonify({'error': 'Rental service unavailable'}), 503
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/rental/<rental_uid>', methods=['DELETE'])
def cancel_rental(rental_uid):
    """Cancel rental with distributed transaction"""
    try:
        username = request.headers.get('X-User-Name')
        if not username:
            return jsonify({'error': 'X-User-Name header is required'}), 400
        
        # Get rental info
        try:
            rental_response = requests.get(
                f'{RENTAL_SERVICE_URL}/api/v1/rental/{rental_uid}',
                headers={'X-User-Name': username},
                timeout=2
            )
            if rental_response.status_code != 200:
                return jsonify({'error': 'Rental not found'}), 404
            rental_info = rental_response.json()
        except requests.exceptions.RequestException:
            return jsonify({'error': 'Rental service unavailable'}), 503
        
        car_uid = rental_info['carUid']
        payment_uid = rental_info['paymentUid']
        
        # Step 1: Free car
        try:
            requests.patch(
                f'{CARS_SERVICE_URL}/api/v1/cars/{car_uid}/availability', 
                json={'availability': True},
                timeout=1
            )
        except requests.exceptions.RequestException:
            # Add to retry queue
            retry_data = {
                'rental_uid': rental_uid,
                'username': username,
                'car_uid': car_uid,
                'payment_uid': payment_uid
            }
            add_to_retry_queue('cancel_rental', retry_data)
            return jsonify({'message': 'Cancellation processing started'}), 202
        
        # Step 2: Cancel payment
        try:
            requests.patch(
                f'{PAYMENT_SERVICE_URL}/api/v1/payments/{payment_uid}',
                timeout=1
            )
        except:
            # Non-critical for user, but log and continue
            pass
        
        # Step 3: Update rental status
        try:
            cancel_response = requests.delete(
                f'{RENTAL_SERVICE_URL}/api/v1/rental/{rental_uid}',
                headers={'X-User-Name': username},
                timeout=2
            )
            return '', cancel_response.status_code
        except requests.exceptions.RequestException:
            return jsonify({'error': 'Rental service unavailable'}), 503
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/manage/circuit-status', methods=['GET'])
def circuit_status():
    """Endpoint to check circuit breaker status"""
    return jsonify(circuit_stats)

if __name__ == '__main__':
    # Start retry queue processor in background thread
    retry_thread = threading.Thread(target=process_retry_queue, daemon=True)
    retry_thread.start()
    
    app.run(host='0.0.0.0', port=8080, debug=False)