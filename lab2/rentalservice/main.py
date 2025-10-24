from quart import Quart
from rental.models.modelr import RentalModel
from rental.getrentals import getrentalsb
from rental.getrental import getrentalb
from rental.postrental import postrentalb
from rental.deleterental import deleterentalb
from rental.postrentalf import postrentalbf
from rental.healthcheck import healthcheckb

app = Quart(__name__)
app.register_blueprint(getrentalb)
app.register_blueprint(getrentalsb)
app.register_blueprint(postrentalb)
app.register_blueprint(deleterentalb)
app.register_blueprint(postrentalbf)
app.register_blueprint(healthcheckb)


def create_tables():
    RentalModel.drop_table()
    RentalModel.create_table()


if __name__ == '__main__':
    create_tables()
    app.run(host='0.0.0.0', port=8060)