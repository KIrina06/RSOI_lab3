import os
import psycopg2
from flask import Flask, request, jsonify
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

def get_db_connection():
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST', 'postgres'),
        database=os.getenv('DB_NAME', 'cars_db'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', 'password'),
        port=os.getenv('DB_PORT', 5432)
    )
    return conn

def check_database_health():
    """Check if database is accessible"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT 1')
        cur.close()
        conn.close()
        return True
    except:
        return False

@app.route('/manage/health', methods=['GET'])
def health_check():
    if check_database_health():
        return jsonify({'status': 'OK'}), 200
    else:
        return jsonify({'status': 'Database connection failed'}), 503

@app.route('/api/v1/cars', methods=['GET'])
def get_cars():
    try:
        page = int(request.args.get('page', 1))
        size = int(request.args.get('size', 10))
        show_all = request.args.get('showAll', 'false').lower() == 'true'
        
        offset = (page - 1) * size
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Get total count
        if show_all:
            cur.execute('SELECT COUNT(*) FROM cars')
        else:
            cur.execute('SELECT COUNT(*) FROM cars WHERE availability = true')
        total_count = cur.fetchone()[0]
        
        # Get cars with pagination
        if show_all:
            cur.execute('SELECT * FROM cars ORDER BY id LIMIT %s OFFSET %s', (size, offset))
        else:
            cur.execute('SELECT * FROM cars WHERE availability = true ORDER BY id LIMIT %s OFFSET %s', (size, offset))
        
        cars = cur.fetchall()
        
        cars_list = []
        for car in cars:
            cars_list.append({
                'carUid': car[1],
                'brand': car[2],
                'model': car[3],
                'registrationNumber': car[4],
                'power': car[5],
                'type': car[7],
                'price': car[6],
                'available': car[8]
            })
        
        cur.close()
        conn.close()
        
        # Return response in the expected format
        return jsonify({
            'page': page,
            'pageSize': len(cars_list),
            'totalElements': total_count,
            'items': cars_list
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/cars/<car_uid>/availability', methods=['PATCH'])
def update_car_availability(car_uid):
    try:
        data = request.get_json()
        availability = data.get('availability')
        
        if availability is None:
            return jsonify({'error': 'Availability field is required'}), 400
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute('UPDATE cars SET availability = %s WHERE car_uid = %s', (availability, car_uid))
        
        if cur.rowcount == 0:
            cur.close()
            conn.close()
            return jsonify({'error': 'Car not found'}), 404
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({'message': 'Car availability updated'}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/cars/<car_uid>', methods=['GET'])
def get_car(car_uid):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute('SELECT * FROM cars WHERE car_uid = %s', (car_uid,))
        car = cur.fetchone()
        
        if not car:
            cur.close()
            conn.close()
            return jsonify({'error': 'Car not found'}), 404
        
        car_data = {
            'carUid': car[1],
            'brand': car[2],
            'model': car[3],
            'registrationNumber': car[4],
            'power': car[5],
            'type': car[7],
            'price': car[6],
            'available': car[8]
        }
        
        cur.close()
        conn.close()
        
        return jsonify(car_data)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8070, debug=False)