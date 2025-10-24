import json
from quart import Blueprint, Response, request
from cars_repository.models.cars_model import CarsModel

get_car_path = Blueprint('get_car', __name__, )


@get_car_path.route('/api/v1/cars/<string:carUid>', methods=['GET'])
async def get_car(carUid: str) -> Response:
    try:
        car = CarsModel.select().where(
            CarsModel.car_uid == carUid
        ).get().to_dict()

        return Response(
            status=200,
            content_type='application/json',
            response=json.dumps(car)
        )
    except:
        return Response(
            status=404,
            content_type='application/json',
            response=json.dumps({
                'errors': ['Uid not found in base.']
            })
        )