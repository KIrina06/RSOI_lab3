import json
from quart import Blueprint, Response, request
from .models.modelc import CarsModel

postcarb = Blueprint('post_car_order', __name__, )


@postcarb.route('/api/v1/cars/<string:carUid>/order', methods=['POST'])
async def post_car_order(carUid: str) -> Response:
    try:
        car = CarsModel.select().where(
            CarsModel.car_uid == carUid
        ).get()

        if car.availability is False:
            return Response(
                status=403,
                content_type='application/json',
                response=json.dumps({
                    'errors': ['Car is booked']
                })
            )

        car.availability = False
        car.save()

        return Response(
            status=200,
            content_type='application/json',
            response=json.dumps(car.to_dict())
        )
    except:
        return Response(
            status=404,
            content_type='application/json',
            response=json.dumps({
                'errors': ['No Uid']
            })
        )