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
