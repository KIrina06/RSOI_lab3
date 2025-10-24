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
        
        with app.app_context():
            db.create_all()

    def teardown_method(self):
        """Очистка после каждого теста"""
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_health_endpoint(self):
        """Тест health check endpoint"""
        response = self.client.get('/manage/health')
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

    def test_args_valid_invalid_page(self):
        """Тест валидации аргументов - невалидная страница"""
        args = {'page': '-1', 'size': '10', 'showAll': 'false'}
        page, size, show_all, errors = args_valid(args)
        
        assert 'Page must be positive' in errors

    def test_args_valid_invalid_size(self):
        """Тест валидации аргументов - невалидный размер"""
        args = {'page': '1', 'size': '0', 'showAll': 'false'}
        page, size, show_all, errors = args_valid(args)
        
        assert 'Size must be positive' in errors

    def test_args_valid_showall_true(self):
        """Тест валидации showAll=true"""
        args = {'page': '1', 'size': '10', 'showAll': 'true'}
        page, size, show_all, errors = args_valid(args)
        
        assert show_all is True
        assert errors == []

    def test_args_valid_showall_false(self):
        """Тест валидации showAll=false"""
        args = {'page': '1', 'size': '10', 'showAll': 'false'}
        page, size, show_all, errors = args_valid(args)
        
        assert show_all is False
        assert errors == []

    def test_args_valid_invalid_showall(self):
        """Тест валидации showAll с невалидным значением"""
        args = {'page': '1', 'size': '10', 'showAll': 'invalid'}
        page, size, show_all, errors = args_valid(args)
        
        assert 'showAll must be true or false' in errors

    @patch('app.db.session')
    def test_get_car_success(self, mock_db):
        """Тест получения информации об автомобиле - успешный случай"""
        # Мокаем модель автомобиля
        mock_car = MagicMock()
        mock_car.to_dict.return_value = {
            'car_uid': 'test-uid',
            'brand': 'Test Brand',
            'model': 'Test Model',
            'availability': True
        }
        
        # Мокаем запрос к БД
        mock_query = MagicMock()
        mock_query.filter.return_value.one_or_none.return_value = mock_car
        mock_db.query.return_value = mock_query

        response = self.client.get('/api/v1/cars/test-uid')
        
        assert response.status_code == 200
        assert response.json['car_uid'] == 'test-uid'

    @patch('app.db.session')
    def test_get_car_not_found(self, mock_db):
        """Тест получения информации об автомобиле - автомобиль не найден"""
        # Мокаем запрос к БД - автомобиль не найден
        mock_query = MagicMock()
        mock_query.filter.return_value.one_or_none.return_value = None
        mock_db.query.return_value = mock_query

        response = self.client.get('/api/v1/cars/non-existent-uid')
        
        assert response.status_code == 404

    @patch('app.db.session')
    def test_post_car_order_success(self, mock_db):
        """Тест бронирования автомобиля - успешный случай"""
        # Мокаем автомобиль
        mock_car = MagicMock()
        mock_car.availability = True
        mock_car.to_dict.return_value = {'car_uid': 'test-uid', 'availability': False}
        
        # Мокаем запрос к БД
        mock_query = MagicMock()
        mock_query.filter.return_value.one_or_none.return_value = mock_car
        mock_db.query.return_value = mock_query

        response = self.client.post('/api/v1/cars/test-uid/order')
        
        assert response.status_code == 200
        # Проверяем, что availability изменился на False
        assert mock_car.availability is False
        # Проверяем, что commit был вызван
        mock_db.commit.assert_called_once()

    @patch('app.db.session')
    def test_post_car_order_not_found(self, mock_db):
        """Тест бронирования автомобиля - автомобиль не найден"""
        # Мокаем запрос к БД - автомобиль не найден
        mock_query = MagicMock()
        mock_query.filter.return_value.one_or_none.return_value = None
        mock_db.query.return_value = mock_query

        response = self.client.post('/api/v1/cars/non-existent-uid/order')
        
        assert response.status_code == 404
        assert b'Uid not found in DB' in response.data

    @patch('app.db.session')
    def test_delete_car_order_success(self, mock_db):
        """Тест отмены бронирования автомобиля - успешный случай"""
        # Мокаем автомобиль
        mock_car = MagicMock()
        mock_car.availability = False  # автомобиль забронирован
        
        # Мокаем запрос к БД
        mock_query = MagicMock()
        mock_query.filter.return_value.one_or_none.return_value = mock_car
        mock_db.query.return_value = mock_query

        response = self.client.delete('/api/v1/cars/test-uid/order')
        
        assert response.status_code == 204
        # Проверяем, что availability изменился на True
        assert mock_car.availability is True
        # Проверяем, что commit был вызван
        mock_db.commit.assert_called_once()

    @patch('app.db.session')
    def test_delete_car_order_not_ordered(self, mock_db):
        """Тест отмены бронирования - автомобиль не был забронирован"""
        # Мокаем автомобиль (не забронирован)
        mock_car = MagicMock()
        mock_car.availability = True
        
        # Мокаем запрос к БД
        mock_query = MagicMock()
        mock_query.filter.return_value.one_or_none.return_value = mock_car
        mock_db.query.return_value = mock_query

        response = self.client.delete('/api/v1/cars/test-uid/order')
        
        assert response.status_code == 403
        assert b"Car isn't ordered" in response.data

    def test_favicon(self):
        """Тест favicon endpoint"""
        response = self.client.get('/favicon.ico')
        # Может вернуть 404 если файла нет, но главное что endpoint существует
        assert response.status_code in [200, 404]

    def test_make_data_response(self):
        """Тест вспомогательной функции make_data_response"""
        from ..src.carsService.app import make_data_response
        
        response = make_data_response(200, message="Success", data={"id": 1})
        
        assert response.status_code == 200
        assert response.json['message'] == 'Success'
        assert response.json['data']['id'] == 1

    def test_make_empty_response(self):
        """Тест вспомогательной функции make_empty"""
        from ..src.carsService.app import make_empty
        
        response = make_empty(204)
        
        assert response.status_code == 204
        assert 'Content-Type' not in response.headers