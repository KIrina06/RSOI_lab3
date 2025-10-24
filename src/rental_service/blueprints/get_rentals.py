import json
from quart import Blueprint, Response, request
from .models.rental_model import RentalModel


get_rentals_blueprint = Blueprint('get_rentals', __name__,)


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

    user = request.headers['X-User-Name']

    rentals = [rental.to_dict() for rental in RentalModel.select().where(RentalModel.username == user)]

    return Response(
        status=200,
        content_type='application/json',
        response=json.dumps(rentals)
    )
