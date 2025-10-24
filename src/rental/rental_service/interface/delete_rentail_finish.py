import json
from quart import Blueprint, Response
from rental_service.models.rental_model import RentalModel

delete_rental_finish_blueprint = Blueprint('delete_rental_finish', __name__, )


@delete_rental_finish_blueprint.route('/api/v1/rental/<string:rentalUid>/finish', methods=['DELETE'])
async def delete_rental_finish(rentalUid: str) -> Response:
    try:
        rental = RentalModel.select().where(
            RentalModel.rental_uid == rentalUid
        ).get()

        if rental.status != 'FINISHED':
            return Response(
                status=403,
                content_type='application/json',
                response=json.dumps({
                    'errors': ['Rental not finished.']
                })
            )

        rental.status = 'IN_PROGRESS'
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
                'errors': ['Uid not found in base.']
            })
        )
