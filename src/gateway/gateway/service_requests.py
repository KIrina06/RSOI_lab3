import requests
from gateway.circuit_breaker import CircuitBreaker

circuit_breaker = CircuitBreaker()


def get_data_from_service(service_url, headers={}, timeout=10):
    if circuit_breaker.try_connect(service_url):
        try:
            response = requests.get(service_url, timeout=timeout, headers=headers)
            circuit_breaker.connection_successful(service_url)
            return response
        except:
            circuit_breaker.connection_error(service_url)
            return None


def post_data_from_service(service_url, headers={}, timeout=10, data={}):
    if circuit_breaker.try_connect(service_url):
        try:
            response = requests.post(service_url, timeout=timeout, headers=headers, json=data)
            circuit_breaker.connection_successful(service_url)
            return response
        except:
            circuit_breaker.connection_error(service_url)
            return None


def delete_data_from_service(service_url, headers={}, timeout=10):
    if circuit_breaker.try_connect(service_url):
        try:
            response = requests.delete(service_url, timeout=timeout, headers=headers)
            circuit_breaker.connection_successful(service_url)
            return response
        except:
            circuit_breaker.connection_error(service_url)
            return None
