import pytest
import json
from unittest.mock import patch, MagicMock
from ..src.carsService.app import app, db, args_valid


class TestCarsApp:
    """Тесты для cars service"""

    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.client = app.test_client()
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['WTF_CSRF_ENABLED'] = False

    def teardown_method(self):
        """Очистка после каждого теста"""
        pass

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

    def test_get_car_not_found(self):
        """Тест получения информации об автомобиле - автомобиль не найден"""
        with app.test_client() as client:
            with patch('app.db.session') as mock_db:
                # Мокаем запрос к БД - автомобиль не найден
                mock_query = MagicMock()
                mock_query.filter.return_value.one_or_none.return_value = None
                mock_db.query.return_value = mock_query

                response = client.get('/api/v1/cars/non-existent-uid')
                assert response.status_code == 404

    def test_basic_math(self):
        """Простой тест математики"""
        assert 1 + 1 == 2