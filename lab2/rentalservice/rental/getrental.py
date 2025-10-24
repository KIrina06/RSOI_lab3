import json
from quart import Blueprint, Response, request
from .models.modelr import RentalModel


getrentalb = Blueprint('get_rental', __name__,)


@getrentalb.route('/api/v1/rental/<string:rentalUid>', methods=['GET'])
async def get_rental(rentalUid: str) -> Response:
    try:
        rental = RentalModel.select().where(
            RentalModel.rental_uid == rentalUid
        ).get().to_dict()

        return Response(
            status=200,
            content_type='application/json',
            response=json.dumps(rental)
        )
    except:
        return Response(
            status=404,
            content_type='application/json',
            response=json.dumps({
                'errors': ['No Uid found']
            })
        )