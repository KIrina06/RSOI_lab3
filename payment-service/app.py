import os
import uuid
import psycopg2
from flask import Flask, request, jsonify
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

def get_db_connection():
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST', 'db-payment'),
        database=os.getenv('DB_NAME', 'payment_db'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', 'password'),
        port=os.getenv('DB_PORT', 5432)
    )
    return conn

@app.route('/manage/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'OK'}), 200

@app.route('/api/v1/payments', methods=['POST'])
def create_payment():
    try:
        data = request.get_json()
        price = data.get('price')
        
        if price is None:
            return jsonify({'error': 'Price field is required'}), 400
        
        payment_uid = str(uuid.uuid4())
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute(
            'INSERT INTO payment (payment_uid, status, price) VALUES (%s, %s, %s) RETURNING id',
            (payment_uid, 'PAID', price)
        )
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({
            'paymentUid': payment_uid,
            'status': 'PAID',
            'price': price
        }), 201
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/payments/<payment_uid>', methods=['GET'])
def get_payment(payment_uid):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute('SELECT * FROM payment WHERE payment_uid = %s', (payment_uid,))
        payment = cur.fetchone()
        
        if not payment:
            cur.close()
            conn.close()
            return jsonify({'error': 'Payment not found'}), 404
        
        payment_data = {
            'paymentUid': payment[1],
            'status': payment[2],
            'price': payment[3]
        }
        
        cur.close()
        conn.close()
        
        return jsonify(payment_data)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/payments/<payment_uid>', methods=['PATCH'])
def cancel_payment(payment_uid):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute('UPDATE payment SET status = %s WHERE payment_uid = %s', ('CANCELED', payment_uid))
        
        if cur.rowcount == 0:
            cur.close()
            conn.close()
            return jsonify({'error': 'Payment not found'}), 404
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({'message': 'Payment canceled'}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8050, debug=True)