import pytest
import json
import os
import sys
from unittest.mock import patch, MagicMock, Mock

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

    def teardown_method(self):
        """Очистка после каждого теста"""
        pass

    def test_health_endpoint(self):
        """Тест health check endpoint"""
        with app.test_client() as client:
            response = client.get('/manage/health')
            assert response.status_code == 200
            assert response.json == {}

    def test_make_data_response(self):
        """Тест вспомогательной функции make_data_response"""
        response = make_data_response(200, message="Success", data={"id": 1})
        
        assert response.status_code == 200
        assert response.json['message'] == 'Success'
        assert response.json['data']['id'] == 1

    def test_make_empty_response(self):
        """Тест вспомогательной функции make_empty"""
        response = make_empty(204)
        
        assert response.status_code == 204
        assert 'Content-Type' not in response.headers

    def test_favicon_endpoint(self):
        """Тест favicon endpoint"""
        with app.test_client() as client:
            response = client.get('/favicon.ico')
            # Может вернуть 404 если файла нет, но главное что endpoint существует
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
            assert response.json['status'] == 'PAID'

    @patch('app.db.session')
    def test_get_payment_not_found(self, mock_db):
        """Тест получения информации о платеже - платеж не найден"""
        # Мокаем запрос к БД - платеж не найден
        mock_query = MagicMock()
        mock_query.filter.return_value.one_or_none.return_value = None
        mock_db.query.return_value = mock_query

        with app.test_client() as client:
            response = client.get('/api/v1/payment/non-existent-uid')
            
            assert response.status_code == 404

    @patch('app.db.session')
    def test_delete_payment_success(self, mock_db):
        """Тест отмены платежа - успешный случай"""
        # Мокаем платеж
        mock_payment = MagicMock()
        mock_payment.status = 'PAID'
        
        # Мокаем запрос к БД
        mock_query = MagicMock()
        mock_query.filter.return_value.one_or_none.return_value = mock_payment
        mock_db.query.return_value = mock_query

        with app.test_client() as client:
            response = client.delete('/api/v1/payment/test-payment-uid')
            
            assert response.status_code == 204
            # Проверяем, что статус изменился на CANCELED
            assert mock_payment.status == 'CANCELED'
            # Проверяем, что commit был вызван
            mock_db.commit.assert_called_once()

    @patch('app.db.session')
    def test_delete_payment_not_found(self, mock_db):
        """Тест отмены платежа - платеж не найден"""
        # Мокаем запрос к БД - платеж не найден
        mock_query = MagicMock()
        mock_query.filter.return_value.one_or_none.return_value = None
        mock_db.query.return_value = mock_query

        with app.test_client() as client:
            response = client.delete('/api/v1/payment/non-existent-uid')
            
            assert response.status_code == 204  # Возвращает 204 даже если не найден

    @patch('app.db.session')
    def test_delete_payment_database_error(self, mock_db):
        """Тест отмены платежа - ошибка базы данных"""
        # Мокаем платеж
        mock_payment = MagicMock()
        mock_payment.status = 'PAID'
        
        # Мокаем запрос к БД
        mock_query = MagicMock()
        mock_query.filter.return_value.one_or_none.return_value = mock_payment
        mock_db.query.return_value = mock_query
        
        # Мокаем ошибку при коммите
        mock_db.commit.side_effect = Exception("DB error")
        
        with app.test_client() as client:
            response = client.delete('/api/v1/payment/test-payment-uid')
            
            assert response.status_code == 500
            assert b'Database delete error' in response.data
            # Проверяем, что rollback был вызван
            mock_db.rollback.assert_called_once()

    @patch('app.db.session')
    @patch('app.uuid4')
    def test_post_payment_success(self, mock_uuid, mock_db):
        """Тест создания платежа - успешный случай"""
        # Мокаем UUID
        mock_uuid.return_value = 'mocked-uuid-1234'
        
        # Мокаем новый платеж
        mock_payment = MagicMock()
        mock_payment.payment_uid = 'mocked-uuid-1234'
        mock_payment.status = 'PAID'
        mock_payment.price = 1500
        mock_payment.to_dict.return_value = {
            'payment_uid': 'mocked-uuid-1234',
            'status': 'PAID',
            'price': 1500
        }
        
        # Мокаем модель платежа
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
                assert response.json['status'] == 'PAID'
                assert response.json['price'] == 1500
                # Проверяем, что платеж был добавлен и закоммичен
                mock_db.add.assert_called_once_with(mock_payment)
                mock_db.commit.assert_called_once()

    def test_post_payment_invalid_json(self):
        """Тест создания платежа - невалидный JSON"""
        with app.test_client() as client:
            response = client.post(
                '/api/v1/payment/',
                data="invalid json",
                content_type='application/json'
            )
            
            # Должен вернуть 500 из-за исключения в коде
            assert response.status_code == 500

    @patch('app.db.session')
    def test_post_payment_database_error(self, mock_db):
        """Тест создания платежа - ошибка базы данных"""
        # Мокаем ошибку при коммите
        mock_db.commit.side_effect = Exception("DB error")
        
        with app.test_client() as client:
            response = client.post(
                '/api/v1/payment/',
                json={'price': 1500},
                content_type='application/json'
            )
            
            assert response.status_code == 500
            assert b'Database post_payment error' in response.data
            # Проверяем, что rollback был вызван
            mock_db.rollback.assert_called_once()

    def test_post_payment_missing_price(self):
        """Тест создания платежа - отсутствует цена"""
        with app.test_client() as client:
            response = client.post(
                '/api/v1/payment/',
                json={},  # нет поля price
                content_type='application/json'
            )
            
            # Должен вернуть 500 из-за KeyError
            assert response.status_code == 500


class TestPaymentModel:
    """Тесты для модели PaymentModel"""
    
    @patch('app.PaymentModel')
    def test_payment_model_creation(self, mock_payment_model):
        """Тест создания модели платежа"""
        mock_instance = MagicMock()
        mock_payment_model.return_value = mock_instance
        
        # Создаем экземпляр
        payment = PaymentModel(
            payment_uid='test-uid',
            status='PAID', 
            price=1000
        )
        
        # Проверяем что модель была создана
        mock_payment_model.assert_called_once()
        
    def test_error_handlers(self):
        """Тест обработчиков ошибок"""
        with app.test_client() as client:
            # Тест несуществующего route
            response = client.get('/non-existent-route')
            assert response.status_code == 404


def test_basic_functionality():
    """Базовые тесты функциональности"""
    # Тест вспомогательных функций
    response = make_data_response(400, error="Bad request")
    assert response.status_code == 400
    assert response.json['error'] == 'Bad request'
    
    response = make_empty(204)
    assert response.status_code == 204