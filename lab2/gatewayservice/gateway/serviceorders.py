import requests


def get_data_from_service(service_url, headers={}, timeout=5):
    try:
        response = requests.get(service_url, timeout=timeout, headers=headers)
        return response
    except:
        return None


def post_data_from_service(service_url, headers={}, timeout=5, data={}):
    try:
        response = requests.post(service_url, timeout=timeout, headers=headers, json=data)
        return response
    except:
        return None


def delete_data_from_service(service_url, headers={}, timeout=5):
    try:
        response = requests.delete(service_url, timeout=timeout, headers=headers)
        return response
    except:
        return None