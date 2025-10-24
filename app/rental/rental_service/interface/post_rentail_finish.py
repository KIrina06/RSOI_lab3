import json
from quart import Blueprint, Response

from rental_service.models.rental_model import RentalModel

post_rental_finish_blueprint = Blueprint('post_rental_finish', __name__, )


@post_rental_finish_blueprint.route('/api/v1/rental/<string:rentalUid>/finish', methods=['POST'])
async def post_rental_finish(rentalUid: str) -> Response:
    try:
        rental = RentalModel.select().where(
            RentalModel.rental_uid == rentalUid
        ).get()

        if rental.status != 'IN_PROGRESS':
            return Response(
                status=403,
                content_type='application/json',
                response=json.dumps({
                    'errors': ['Rental not in progres.']
                })
            )

        rental.status = 'FINISHED'
        resp = json.dumps(rental.to_dict())
        rental.save()

        return Response(
            status=200,
            content_type='application/json',
            response=resp
        )
    except Exception as e:
        return Response(
            status=404,
            content_type='application/json',
            response=json.dumps({
                'errors': ['Uid not found in base.']
            })
        )
