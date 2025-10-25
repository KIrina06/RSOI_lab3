import os
import uuid
import psycopg2
from datetime import datetime
from flask import Flask, request, jsonify
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

def get_db_connection():
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST', 'postgres'),
        database=os.getenv('DB_NAME', 'rental_db'),
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

@app.route('/api/v1/rental', methods=['GET'])
def get_rentals():
    try:
        username = request.headers.get('X-User-Name')
        if not username:
            return jsonify({'error': 'X-User-Name header is required'}), 400
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute('SELECT * FROM rental WHERE username = %s ORDER BY date_from DESC', (username,))
        rentals = cur.fetchall()
        
        rentals_list = []
        for rental in rentals:
            rentals_list.append({
                'rentalUid': rental[1],
                'status': rental[7],
                'dateFrom': rental[5].strftime('%Y-%m-%d'),
                'dateTo': rental[6].strftime('%Y-%m-%d'),
                'carUid': rental[4],
                'paymentUid': rental[3]
            })
        
        cur.close()
        conn.close()
        
        return jsonify(rentals_list)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/rental/<rental_uid>', methods=['GET'])
def get_rental(rental_uid):
    try:
        username = request.headers.get('X-User-Name')
        if not username:
            return jsonify({'error': 'X-User-Name header is required'}), 400
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute('SELECT * FROM rental WHERE rental_uid = %s AND username = %s', (rental_uid, username))
        rental = cur.fetchone()
        
        if not rental:
            cur.close()
            conn.close()
            return jsonify({'error': 'Rental not found'}), 404
        
        rental_data = {
            'rentalUid': rental[1],
            'status': rental[7],
            'dateFrom': rental[5].strftime('%Y-%m-%d'),
            'dateTo': rental[6].strftime('%Y-%m-%d'),
            'carUid': rental[4],
            'paymentUid': rental[3]
        }
        
        cur.close()
        conn.close()
        
        return jsonify(rental_data)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/rental', methods=['POST'])
def create_rental():
    try:
        username = request.headers.get('X-User-Name')
        if not username:
            return jsonify({'error': 'X-User-Name header is required'}), 400
        
        data = request.get_json()
        car_uid = data.get('carUid')
        date_from = data.get('dateFrom')
        date_to = data.get('dateTo')
        payment_uid = data.get('paymentUid')
        status = data.get('status', 'IN_PROGRESS')
        
        if not all([car_uid, date_from, date_to, payment_uid]):
            return jsonify({'error': 'carUid, dateFrom, dateTo, and paymentUid are required'}), 400
        
        # Создаем аренду
        rental_uid = str(uuid.uuid4())
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute(
            'INSERT INTO rental (rental_uid, username, payment_uid, car_uid, date_from, date_to, status) VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id',
            (rental_uid, username, payment_uid, car_uid, date_from, date_to, status)
        )
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({
            'rentalUid': rental_uid,
            'status': status,
            'dateFrom': date_from,
            'dateTo': date_to,
            'carUid': car_uid,
            'paymentUid': payment_uid
        }), 201
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/rental/<rental_uid>/finish', methods=['POST'])
def finish_rental(rental_uid):
    try:
        username = request.headers.get('X-User-Name')
        if not username:
            return jsonify({'error': 'X-User-Name header is required'}), 400
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Обновляем статус аренды
        cur.execute('UPDATE rental SET status = %s WHERE rental_uid = %s AND username = %s', 
                   ('FINISHED', rental_uid, username))
        
        if cur.rowcount == 0:
            cur.close()
            conn.close()
            return jsonify({'error': 'Rental not found'}), 404
        
        conn.commit()
        cur.close()
        conn.close()
        
        return '', 204
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/rental/<rental_uid>', methods=['DELETE'])
def cancel_rental(rental_uid):
    try:
        username = request.headers.get('X-User-Name')
        if not username:
            return jsonify({'error': 'X-User-Name header is required'}), 400
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Обновляем статус аренды
        cur.execute('UPDATE rental SET status = %s WHERE rental_uid = %s AND username = %s', 
                   ('CANCELED', rental_uid, username))
        
        if cur.rowcount == 0:
            cur.close()
            conn.close()
            return jsonify({'error': 'Rental not found'}), 404
        
        conn.commit()
        cur.close()
        conn.close()
        
        return '', 204
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8060, debug=False)