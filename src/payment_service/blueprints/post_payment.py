import uuid
import json
from quart import Blueprint, Response, request
from .models.payment_model import PaymentModel


post_payment_blueprint = Blueprint('post_payment', __name__,)


def validate_body(body):
    try:
        body = json.loads(body)
    except:
        return None, ['Can\'t deserialize body!']

    errors = []
    if 'price' not in body.keys() or type(body['price']) is not int:
        return None, ['Bad structure body!']

    return body, errors


@post_payment_blueprint.route('/api/v1/payment/', methods=['POST'])
async def post_payment() -> Response:
    body, errors = validate_body(await request.body)
    if len(errors) > 0:
        return Response(
            status=400,
            content_type='application/json',
            response=json.dumps(errors)
        )

    payment = PaymentModel.create(
        payment_uid=uuid.uuid4(),
        price=body['price'],
        status='PAID'
    )

    return Response(
        status=200,
        content_type='application/json',
        response=json.dumps(payment.to_dict())
    )
