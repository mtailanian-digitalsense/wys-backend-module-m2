from lib import app, db, abort, request
from flask_swagger import swagger
from flask_swagger_ui import get_swaggerui_blueprint

if __name__ == '__main__':
    app.run()
    app.debug = True

