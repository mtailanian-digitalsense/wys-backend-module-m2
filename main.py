import jwt
import requests
from lib import app, db, abort, jsonify, request, area_calc
from flask_swagger import swagger
from flask_swagger_ui import get_swaggerui_blueprint
from functools import wraps

# Loading Config Parameters
APP_HOST = os.getenv('APP_HOST', '127.0.0.1')
APP_PORT = os.getenv('APP_PORT', 5001)
SPACES_MODULE_HOST = os.getenv('SPACES_MODULE_IP', '127.0.0.1')
SPACES_MODULE_PORT = os.getenv('SPACES_MODULE_PORT', 5002)

app.config['SECRET_KEY']= 'Th1s1ss3cr3t'


class M2Generated(db.Model):
    """
    M2Generated.
    Represents the values configured by the user and calculated according to them.

    Attributes
    ----------
    id: Represent the unique id of a M2 generated
    hot_desking_level: Value of Hot Desking Level
    collaborative_level: Value of the Collaborative Level
    workers_num: Value of Workers number
    area: Value of calculated Area
    density: Area density value
    """
    id = db.Column(db.Integer, primary_key=True)
    hot_desking_level = db.Column(db.Integer, nullable=False)
    collaborative_level = db.Column(db.Integer, nullable=False)
    workers_num = db.Column(db.Integer, nullable=False)
    area = db.Column(db.Float, nullable=False)
    density = db.Column(db.Float, nullable=False)

# Swagger Config

SWAGGER_URL = '/api/m2/docs/'
API_URL = '/api/m2/spec'
swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={  # Swagger UI config overrides
        'app_name': "WYS Api. Project Service"
    }
)

app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

def token_required(f):  
    @wraps(f)  
    def decorator(*args, **kwargs):

        token = request.headers.get('Authorization', None)
        if not token:
            app.logger.debug("token_required")
            return jsonify({'message': 'a valid token is missing'})
        app.logger.debug("Token: " + token)
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        except:  
            return jsonify({'message': 'token is invalid'})  
        
        return f(*args,  **kwargs)
    return decorator

@app.route("/api/m2/spec", methods=['GET'])
@token_required
def spec():
    return jsonify(swagger(app))

@app.route('/api/m2', methods = ['POST'])
@token_required
def get_m2_value():
    """
        Get m2 area
        ---
        produces:
        - "application/json"
        parameters:
        - in: "body"
          name: "body"
          description: "Data required for M2 area to be generated"
          required: true
        responses:
          201:
            description: "Area value"
          500:
            description: "Server error"
    """
    if not request.json or (not 'hotdesking_level' and not 'colaboration_level' and not 'num_of_workers') in request.json:
        abort(400)
    
    try:
        hotdesking_level = request.json['hotdesking_level']
        colaboration_level = request.json['colaboration_level']
        workers_num = request.json['num_of_workers']

        area = area_calc(hotdesking_level, colaboration_level, workers_num)

        if(area):
            return jsonify({'area': area}), 200

        return jsonify({'message': "Error, the area could not be calculated. Try again."}), 500
    
    except Exception as exp:
        app.logger.error(f"Error in database: mesg ->{exp}")
        return exp, 500

@app.route('/api/m2/generate', methods = ['POST'])
@token_required
def generate_workspace():
    pass

if __name__ == '__main__':
    app.run(host= APP_HOST, port = APP_PORT, debug = True)