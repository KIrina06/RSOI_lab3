from quart import Quart
from gateway.getcars import getcarsb
from gateway.getrentals import getrentalsb
from gateway.getrental import getrentalb
from gateway.postrental import postrentalsb
from gateway.deleterental import deleterentalb
from gateway.postrentalf import postrentalbf
from gateway.healthcheck import healthcheckb

app = Quart(__name__)
app.register_blueprint(getcarsb)
app.register_blueprint(getrentalsb)
app.register_blueprint(postrentalsb)
app.register_blueprint(deleterentalb)
app.register_blueprint(postrentalbf)
app.register_blueprint(getrentalb)
app.register_blueprint(healthcheckb)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)