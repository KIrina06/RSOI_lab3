
import os
import json

from quart import Blueprint, Response, request
from gateway.service_requests import get_data_from_service

get_rentals_blueprint = Blueprint('get_rentals', __name__, )


def car_simplify(car: dict) -> dict:
    return {
        "carUid": car['carUid'],
        "brand": car['brand'],
        "model": car['model'],
        "registrationNumber": car['registrationNumber']
    }


@get_rentals_blueprint.route('/api/v1/rental/', methods=['GET'])
async def get_rentals() -> Response:
    if 'X-User-Name' not in request.headers.keys():
        return Response(
            status=400,
            content_type='application/json',
            response=json.dumps({
                'errors': ['Request has not X-User-Name header!']
            })
        )

    response = get_data_from_service(
        'http://' + os.environ['RENTAL_SERVICE_HOST'] + ':' + os.environ['RENTAL_SERVICE_PORT']
        + '/api/v1/rental', timeout=10, headers={'X-User-Name': request.headers['X-User-Name']})
    if response is None:
        return Response(
            status=503,
            content_type='application/json',
            response=json.dumps({
                'errors': ['Rental service is unavailable.']
            })
        )

    rentals = response.json()
    for rental in rentals:
        response = get_data_from_service(
            'http://' + os.environ['CARS_SERVICE_HOST'] + ':' + os.environ['CARS_SERVICE_PORT']
            + '/api/v1/cars/' + rental['carUid'], timeout=10)

        if response is not None and response.status_code == 200:
            rental['car'] = car_simplify(response.json())
        else:
            rental['car'] = rental['carUid']
        del rental['carUid']

        response = get_data_from_service(
            'http://' + os.environ['PAYMENT_SERVICE_HOST'] + ':' + os.environ['PAYMENT_SERVICE_PORT']
            + '/api/v1/payment/' + rental['paymentUid'], timeout=10)

        if response is not None and response.status_code == 200:
            rental['payment'] = response.json()
        else:
            rental['payment'] = rental['paymentUid']
        del rental['paymentUid']

    return Response(
        status=200,
        content_type='application/json',
        response=json.dumps(rentals)
    )