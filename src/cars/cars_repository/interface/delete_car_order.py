import json
from quart import Blueprint, Response, request
from cars_repository.models.cars_model import CarsModel

delete_car_order_path = Blueprint('delete_car_order', __name__, )


@delete_car_order_path.route('/api/v1/cars/<string:carUid>/order', methods=['DELETE'])
async def delete_car_order(carUid: str) -> Response:
    try:
        car = CarsModel.select().where(
            CarsModel.car_uid == carUid
        ).get()

        if car.availability is True:
            return Response(
                status=403,
                content_type='application/json',
                response=json.dumps({
                    'errors': ['Car isn\'t ordered.']
                })
            )

        car.availability = True
        car.save()

        return Response(
            status=200
        )
    except:
        return Response(
            status=404,
            content_type='application/json',
            response=json.dumps({
                'errors': ['Uid not found in base.']
            })
        )