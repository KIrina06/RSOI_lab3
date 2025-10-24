from quart import Quart
from cars.models.modelc import CarsModel
from cars.getcars import getcarsb
from cars.getcar import getcarb
from cars.postcar import postcarb
from cars.deletecar import deletecarb
from cars.healthcheck import healthcheckb

app = Quart(__name__)
app.register_blueprint(getcarsb)
app.register_blueprint(getcarb)
app.register_blueprint(postcarb)
app.register_blueprint(deletecarb)
app.register_blueprint(healthcheckb)


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