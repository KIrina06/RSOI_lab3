import json
from quart import Blueprint, Response, request
from .models.payment_model import PaymentModel


get_payment_blueprint = Blueprint('get_payment', __name__,)


@get_payment_blueprint.route('/api/v1/payment/<string:paymentUid>', methods=['GET'])
async def get_payment(paymentUid: str) -> Response:
    try:
        payment = PaymentModel.select().where(
            PaymentModel.payment_uid == paymentUid
        ).get().to_dict()

        return Response(
            status=200,
            content_type='application/json',
            response=json.dumps(payment)
        )
    except:
        return Response(
            status=404,
            content_type='application/json',
            response=json.dumps({
                'errors': ['Uid not found in base.']
            })
        )
