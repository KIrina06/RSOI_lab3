from quart import Quart
from blueprints.models.cars_model import CarsModel
from blueprints.get_cars import get_cars_blueprint
from blueprints.get_car import get_car_blueprint
from blueprints.post_car_order import post_car_order_blueprint
from blueprints.delete_car_order import delete_car_order_blueprint
from blueprints.health_check_blueprint import health_check_blueprint

app = Quart(__name__)
app.register_blueprint(get_cars_blueprint)
app.register_blueprint(get_car_blueprint)
app.register_blueprint(post_car_order_blueprint)
app.register_blueprint(delete_car_order_blueprint)
app.register_blueprint(health_check_blueprint)


def create_tables():
    CarsModel.drop_table()
    CarsModel.create_table()

    CarsModel.get_or_create(
        id=1,
        car_uid="109b42f3-198d-4c89-9276-a7520a7120ab",
        brand="Mercedes Benz",
        model="GLA 250",
        registration_number="ЛО777Х799",
        power=249,
        type="SEDAN",
        price=3500,
        availability=True
    )


if __name__ == '__main__':
    create_tables()
    app.run(host='0.0.0.0', port=8070)
