import pytest
import json
import os
import sys
from unittest.mock import patch, MagicMock

# Добавляем путь к исходному коду
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'carsService'))

from app import app, db, args_valid, make_data_response, make_empty


class TestCarsApp:
    """Тесты для cars service"""

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

    def test_args_valid_success(self):
        """Тест валидации аргументов - успешный случай"""
        args = {'page': '1', 'size': '10', 'showAll': 'false'}
        page, size, show_all, errors = args_valid(args)
        
        assert page == 1
        assert size == 10
        assert show_all is False
        assert errors == []

    def test_args_valid_missing_required(self):
        """Тест валидации аргументов - отсутствуют обязательные поля"""
        args = {'page': '1'}  # отсутствует size
        page, size, show_all, errors = args_valid(args)
        
        assert 'Size must be define' in errors
        assert len(errors) > 0

    def test_make_data_response_within_context(self):
        """Тест make_data_response внутри контекста приложения"""
        with app.app_context():
            response = make_data_response(200, message="Success", data={"id": 1})
            assert response.status_code == 200
            assert response.json['message'] == 'Success'

    def test_make_empty_within_context(self):
        """Тест make_empty внутри контекста приложения"""
        with app.app_context():
            response = make_empty(204)
            assert response.status_code == 204
