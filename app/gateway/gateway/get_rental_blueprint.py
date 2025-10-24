import os
import json

from quart import Blueprint, Response, request
from gateway.service_requests import get_data_from_service

get_rental_blueprint = Blueprint('get_rental', __name__, )


def car_simplify(car: dict) -> dict:
    return {
        "carUid": car['carUid'],
        "brand": car['brand'],
        "model": car['model'],
        "registrationNumber": car['registrationNumber']
    }


@get_rental_blueprint.route('/api/v1/rental/<string:rentalUid>', methods=['GET'])
async def get_rental(rentalUid: str) -> Response:
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
        + '/api/v1/rental/'+rentalUid, timeout=10, headers={'X-User-Name': request.headers['X-User-Name']})
    if response is None:
        return Response(
            status=503,
            content_type='application/json',
            response=json.dumps({
                'errors': ['Rental service is unavailable.']
            })
        )
    elif int(response.status_code / 100) != 2:
        return Response(
            status=response.status_code,
            content_type='application/json',
            response=response.text
        )

    rental = response.json()

    response = get_data_from_service(
        'http://' + os.environ['CARS_SERVICE_HOST'] + ':' + os.environ['CARS_SERVICE_PORT']
        + '/api/v1/cars/' + rental['carUid'], timeout=10)
    if response is None:
        rental['car'] = rental['carUid']
    elif int(response.status_code / 100) == 2:
        rental['car'] = car_simplify(response.json())
    else:
        return Response(
            status=response.status_code,
            content_type='application/json',
            response=response.text
        )
    del rental['carUid']

    response = get_data_from_service(
        'http://' + os.environ['PAYMENT_SERVICE_HOST'] + ':' + os.environ['PAYMENT_SERVICE_PORT']
        + '/api/v1/payment/' + rental['paymentUid'], timeout=10)
    if response is None:
        rental['payment'] = {}
    elif int(response.status_code / 100) == 2:
        rental['payment'] = response.json()
    else:
        return Response(
            status=response.status_code,
            content_type='application/json',
            response=response.text
        )

    del rental['paymentUid']

    return Response(
        status=200,
        content_type='application/json',
        response=json.dumps(rental)
    )
