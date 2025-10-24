import json
from quart import Blueprint, Response, request
from .models.payment_model import PaymentModel


delete_current_payment_blueprint = Blueprint('delete_current_payment', __name__,)


@delete_current_payment_blueprint.route('/api/v1/payment/<string:paymentUid>', methods=['DELETE'])
async def get_current_payment(paymentUid: str) -> Response:
    try:
        payment = PaymentModel.select().where(
            PaymentModel.payment_uid == paymentUid
        ).get()

        payment.status = 'CANCELED'
        payment.save()

        return Response(
            status=200,
            content_type='application/json',
            response=json.dumps(payment.to_dict())
        )
    except:
        return Response(
            status=404,
            content_type='application/json',
            response=json.dumps({
                'errors': ['Uid not found in base.']
            })
        )