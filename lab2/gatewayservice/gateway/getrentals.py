import os
import json

from quart import Blueprint, Response, request
from .serviceorders import get_data_from_service

getrentalsb = Blueprint('get_rentals', __name__, )


def car_simplify(car: dict) -> dict:
    return {
        "carUid": car['carUid'],
        "brand": car['brand'],
        "model": car['model'],
        "registrationNumber": car['registrationNumber']
    }


@getrentalsb.route('/api/v1/rental/', methods=['GET'])
async def get_rentals() -> Response:
    if 'X-User-Name' not in request.headers.keys():
        return Response(
            status=400,
            content_type='application/json',
            response=json.dumps({
                'errors': ['wrong user name']
            })
        )

    response = get_data_from_service(
        'http://' + os.environ['RENTAL_SERVICE_HOST'] + ':' + os.environ['RENTAL_SERVICE_PORT']
        + '/api/v1/rental', timeout=5, headers={'X-User-Name': request.headers['X-User-Name']})
    if response is None:
        return Response(
            status=500,
            content_type='application/json',
            response=json.dumps({
                'errors': ['service not working']
            })
        )

    rentals = response.json()
    for rental in rentals:
        response = get_data_from_service(
            'http://' + os.environ['CARS_SERVICE_HOST'] + ':' + os.environ['CARS_SERVICE_PORT']
            + '/api/v1/cars/' + rental['carUid'], timeout=5)
        if response is None:
            return Response(
                status=500,
                content_type='application/json',
                response=json.dumps({
                    'errors': ['service not working']
                })
            )
        del rental['carUid']
        rental['car'] = car_simplify(response.json())

        response = get_data_from_service(
            'http://' + os.environ['PAYMENT_SERVICE_HOST'] + ':' + os.environ['PAYMENT_SERVICE_PORT']
            + '/api/v1/payment/' + rental['paymentUid'], timeout=5)
        if response is None:
            return Response(
                status=500,
                content_type='application/json',
                response=json.dumps({
                    'errors': ['service not working']
                })
            )
        rental['payment'] = response.json()
        del rental['paymentUid']

    return Response(
        status=200,
        content_type='application/json',
        response=json.dumps(rentals)
    )