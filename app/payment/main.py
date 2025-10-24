from quart import Quart
import psycopg2
from payment_service.models.payment_model import PaymentModel
from payment_service.interface.get_payment import get_payment_blueprint
from payment_service.interface.post_payment import post_payment_blueprint
from payment_service.interface.delete_payment import delete_current_payment_blueprint
from payment_service.interface.health_check_blueprint import health_check_blueprint

app = Quart(__name__)
app.register_blueprint(get_payment_blueprint)
app.register_blueprint(post_payment_blueprint)
app.register_blueprint(delete_current_payment_blueprint)
app.register_blueprint(health_check_blueprint)


def create_tables():
    PaymentModel.create_table()


if __name__ == '__main__':
    create_tables()
    app.run(host='0.0.0.0',port=8050)
