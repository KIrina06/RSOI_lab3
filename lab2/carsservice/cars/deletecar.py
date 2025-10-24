import json
from quart import Blueprint, Response
from .models.modelc import CarsModel

deletecarb = Blueprint('delete_car_order', __name__, )


@deletecarb.route('/api/v1/cars/<string:carUid>/order', methods=['DELETE'])
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
                    'errors': ['Car not requested']
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
                'errors': ['No Uid']
            })
        )