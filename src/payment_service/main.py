from quart import Quart
from blueprints.models.payment_model import PaymentModel
from blueprints.get_payment import get_payment_blueprint
from blueprints.post_payment import post_payment_blueprint
from blueprints.delete_payment import delete_current_payment_blueprint
from blueprints.health_check_blueprint import health_check_blueprint

app = Quart(__name__)
app.register_blueprint(get_payment_blueprint)
app.register_blueprint(post_payment_blueprint)
app.register_blueprint(delete_current_payment_blueprint)
app.register_blueprint(health_check_blueprint)


def create_tables():
    # PaymentModel.drop_table()
    PaymentModel.create_table()


if __name__ == '__main__':
    create_tables()
    app.run(host='0.0.0.0',port=8050)
