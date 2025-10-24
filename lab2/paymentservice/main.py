from quart import Quart
from payment.models.modelp import PaymentModel
from payment.getpayment import getpaymentb
from payment.postpayment import postpaymentb
from payment.deletepayment import deletepaymentb
from payment.healthcheck import healthcheckb

app = Quart(__name__)
app.register_blueprint(getpaymentb)
app.register_blueprint(postpaymentb)
app.register_blueprint(deletepaymentb)
app.register_blueprint(healthcheckb)


def create_tables():
    PaymentModel.drop_table()
    PaymentModel.create_table()


if __name__ == '__main__':
    create_tables()
    app.run(host='0.0.0.0',port=8050)