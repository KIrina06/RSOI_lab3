from quart import Quart
from blueprints.models.rental_model import RentalModel
from blueprints.get_rentals import get_rentals_blueprint
from blueprints.get_rental import get_rental_blueprint
from blueprints.post_rental import post_rental_blueprint
from blueprints.delete_rental import delete_current_rental_blueprint
from blueprints.post_rentail_finish import post_rental_finish_blueprint
from blueprints.delete_rentail_finish import delete_rental_finish_blueprint
from blueprints.health_check_blueprint import health_check_blueprint

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
