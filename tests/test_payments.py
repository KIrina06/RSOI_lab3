import pytest
import json
import os
import sys
from unittest.mock import patch, MagicMock

# Добавляем путь к исходному коду
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'paymentService'))

from app import app, db, make_data_response, make_empty


class TestPaymentApp:
    """Тесты для payment service"""

    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.client = app.test_client()
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    def test_health_endpoint(self):
        """Тест health check endpoint"""
        with app.test_client() as client:
            response = client.get('/manage/health')
            assert response.status_code == 200
            assert response.json == {}

    def test_make_data_response_within_context(self):
        """Тест make_data_response внутри контекста приложения"""
        with app.app_context():
            response = make_data_response(200, message="Success", data={"id": 1})
            assert response.status_code == 200
            assert response.json['message'] == 'Success'
            assert response.json['data']['id'] == 1

    def test_make_empty_within_context(self):
        """Тест make_empty внутри контекста приложения"""
        with app.app_context():
            response = make_empty(204)
            assert response.status_code == 204
            assert 'Content-Type' not in response.headers

    def test_favicon_endpoint(self):
        """Тест favicon endpoint"""
        with app.test_client() as client:
            response = client.get('/favicon.ico')
            assert response.status_code in [200, 404]

    @patch('app.db.session')
    def test_get_payment_success(self, mock_db):
        """Тест получения информации о платеже - успешный случай"""
        # Мокаем платеж
        mock_payment = MagicMock()
        mock_payment.to_dict.return_value = {
            'payment_uid': 'test-payment-uid',
            'status': 'PAID',
            'price': 1000
        }
        
        # Мокаем запрос к БД
        mock_query = MagicMock()
        mock_query.filter.return_value.one_or_none.return_value = mock_payment
        mock_db.query.return_value = mock_query

        with app.test_client() as client:
            response = client.get('/api/v1/payment/test-payment-uid')
            assert response.status_code == 200
            assert response.json['payment_uid'] == 'test-payment-uid'

    @patch('app.db.session')
    def test_get_payment_not_found(self, mock_db):
        """Тест получения информации о платеже - платеж не найден"""
        mock_query = MagicMock()
        mock_query.filter.return_value.one_or_none.return_value = None
        mock_db.query.return_value = mock_query

        with app.test_client() as client:
            response = client.get('/api/v1/payment/non-existent-uid')
            assert response.status_code == 404

    @patch('app.db.session')
    def test_delete_payment_success(self, mock_db):
        """Тест отмены платежа - успешный случай"""
        mock_payment = MagicMock()
        mock_payment.status = 'PAID'
        
        mock_query = MagicMock()
        mock_query.filter.return_value.one_or_none.return_value = mock_payment
        mock_db.query.return_value = mock_query

        with app.test_client() as client:
            response = client.delete('/api/v1/payment/test-payment-uid')
            assert response.status_code == 204
            assert mock_payment.status == 'CANCELED'
            mock_db.commit.assert_called_once()

    @patch('app.db.session')
    @patch('app.uuid4')
    def test_post_payment_success(self, mock_uuid, mock_db):
        """Тест создания платежа - успешный случай"""
        mock_uuid.return_value = 'mocked-uuid-1234'
        
        mock_payment = MagicMock()
        mock_payment.payment_uid = 'mocked-uuid-1234'
        mock_payment.status = 'PAID'
        mock_payment.price = 1500
        mock_payment.to_dict.return_value = {
            'payment_uid': 'mocked-uuid-1234',
            'status': 'PAID',
            'price': 1500
        }
        
        with patch('app.PaymentModel') as mock_payment_model:
            mock_payment_model.return_value = mock_payment
            
            with app.test_client() as client:
                response = client.post(
                    '/api/v1/payment/',
                    json={'price': 1500},
                    content_type='application/json'
                )
                
                assert response.status_code == 201
                assert response.json['payment_uid'] == 'mocked-uuid-1234'


class TestHelperFunctions:
    """Тесты вспомогательных функций с правильным контекстом"""
    
    def test_make_data_response_different_status_codes(self):
        """Тест make_data_response с разными кодами статуса"""
        with app.app_context():
            # Тест успешного ответа
            response = make_data_response(200, message="OK")
            assert response.status_code == 200
            
            # Тест ошибки клиента
            response = make_data_response(400, error="Bad Request")
            assert response.status_code == 400
            
            # Тест ошибки сервера
            response = make_data_response(500, error="Internal Server Error")
            assert response.status_code == 500

    def test_make_empty_different_status_codes(self):
        """Тест make_empty с разными кодами статуса"""
        with app.app_context():
            for status_code in [200, 201, 204, 400]:
                response = make_empty(status_code)
                assert response.status_code == status_code
                assert 'Content-Type' not in response.headers
