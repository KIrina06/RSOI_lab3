import json
from quart import Blueprint, Response
from .models.modelp import PaymentModel


getpaymentb = Blueprint('get_payment', __name__,)


@getpaymentb.route('/api/v1/payment/<string:paymentUid>', methods=['GET'])
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
                'errors': ['No Uid']
            })
        )