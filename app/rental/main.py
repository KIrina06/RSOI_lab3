from quart import Quart
import psycopg2

from rental_service.interface.delete_rentail_finish import delete_rental_finish_blueprint
from rental_service.models.rental_model import RentalModel
from rental_service.interface.get_rentals import get_rentals_blueprint
from rental_service.interface.get_rental import get_rental_blueprint
from rental_service.interface.post_rental import post_rental_blueprint
from rental_service.interface.delete_rental import delete_current_rental_blueprint
from rental_service.interface.post_rentail_finish import post_rental_finish_blueprint
from rental_service.interface.health_check_blueprint import health_check_blueprint

app = Quart(__name__)
app.register_blueprint(get_rental_blueprint)
app.register_blueprint(get_rentals_blueprint)
app.register_blueprint(post_rental_blueprint)
app.register_blueprint(delete_current_rental_blueprint)
app.register_blueprint(post_rental_finish_blueprint)
app.register_blueprint(delete_rental_finish_blueprint)
app.register_blueprint(health_check_blueprint)


def create_tables():
    RentalModel.drop_table()
    RentalModel.create_table()


if __name__ == '__main__':
    create_tables()
    app.run(host='0.0.0.0', port=8060)
