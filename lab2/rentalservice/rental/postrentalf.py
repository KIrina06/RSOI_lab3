import json
from quart import Blueprint, Response, request
from .models.modelr import RentalModel

postrentalbf = Blueprint('post_rental_finish', __name__, )


@postrentalbf.route('/api/v1/rental/<string:rentalUid>/finish', methods=['POST'])
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
                    'errors': ['error not in progres']
                })
            )

        rental.status = 'FINISHED'
        rental.save()

        return Response(
            status=204,
            content_type='application/json',
            response=json.dumps(rental.to_dict())
        )
    except Exception as e:
        return Response(
            status=404,
            content_type='application/json',
            response=json.dumps({
                'errors': ['No Uid found']
            })
        )