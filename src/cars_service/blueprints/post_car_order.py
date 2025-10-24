import json
from quart import Blueprint, Response, request
from .models.cars_model import CarsModel

post_car_order_blueprint = Blueprint('post_car_order', __name__, )


@post_car_order_blueprint.route('/api/v1/cars/<string:carUid>/order', methods=['POST'])
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
                    'errors': ['Car is already ordered.']
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
                'errors': ['Uid not found in base.']
            })
        )