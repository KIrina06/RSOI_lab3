from quart import Quart
import psycopg2
from cars_repository.models.cars_model import CarsModel
from cars_repository.interface.get_cars import get_cars_path
from cars_repository.interface.get_car import get_car_path
from cars_repository.interface.post_car_order import post_car_order_path
from cars_repository.interface.delete_car_order import delete_car_order_path
from cars_repository.interface.health_check import health_check_cars

app = Quart(__name__)
app.register_blueprint(get_cars_path)
app.register_blueprint(get_car_path)
app.register_blueprint(post_car_order_path)
app.register_blueprint(delete_car_order_path)
app.register_blueprint(health_check_cars)


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
