import jwt
import requests
import json
import math
from lib import app, os, db, abort, jsonify, request, num_private_office, total_open_plan, num_formal_collaborative, num_informal_collaborative, num_phonebooth, area_calc, M2InternalConfigVar
from flask_swagger import swagger
from flask_swagger_ui import get_swaggerui_blueprint
from functools import wraps

# Loading Config Parameters
APP_HOST = os.getenv('APP_HOST', '127.0.0.1')
APP_PORT = os.getenv('APP_PORT', 5001)
SPACES_MODULE_HOST = os.getenv('SPACES_MODULE_IP', '127.0.0.1')
SPACES_MODULE_PORT = os.getenv('SPACES_MODULE_PORT', 5002)
SPACES_MODULE_API_CREATE = os.getenv('SPACES_MODULE_API_CREATE', '/api/spaces/create')

try:
    f = open('oauth-public.key', 'r')
    key: str = f.read()
    f.close()
    app.config['SECRET_KEY'] = key
except Exception as e:
    app.logger.error(f'Can\'t read public key f{e}')
    exit(-1)


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

def round_half_up(n, decimals=0):
    multiplier = 10 ** decimals
    return math.floor(n*multiplier + 0.5) / multiplier

def obs_and_quantity_calculator(category_name, subcategory, hotdesking, grade_of_collaboration, workers_number, area):
    if(category_name == "Colaborativo"):
        obs_switcher = {
            "Colaborativo":{
                "Pequeño": num_informal_collaborative(hotdesking, grade_of_collaboration, workers_number)*0.2,
                "Mediano": num_informal_collaborative(hotdesking, grade_of_collaboration, workers_number)*0.3,
                "Grande": num_informal_collaborative(hotdesking, grade_of_collaboration, workers_number)*0.5
            }
        }
        obs = obs_switcher[category_name][subcategory['name']]
    elif(category_name == "Sala Reunión"):
        obs = num_formal_collaborative(hotdesking, grade_of_collaboration, workers_number) * subcategory['usage_percentage']
    else:
        obs = None

    if(category_name == "Puesto de Trabajo"):
        quantity = round_half_up(total_open_plan(hotdesking, workers_number))
    elif(category_name == "Soporte" and subcategory['name'] == "Baño Individual"):
        if(workers_number < 11):
            quantity = 1
        elif(11 <= workers_number < 31):
            quantity = 2
        elif(31 <= workers_number < 51):
            quantity = 3
        elif(51 <= workers_number < 71):
            quantity = 4
        elif(71 <= workers_number < 91):
            quantity = 5
        elif(91 <= workers_number < 101):
            quantity = 6
        else:
            quantity = round_half_up(6 + ((workers_number-100)/15))
    elif(category_name == "Sala Reunión"):
        quantity = round_half_up(obs/subcategory['people_capacity'])
    else:
        quantity_switcher = {
            "Privado":{
                "Pequeño": round_half_up(num_private_office(hotdesking, workers_number)*0.7),
                "Grande": round_half_up(num_private_office(hotdesking, workers_number)*0.3)
            },
            "Recepción":{
                "Pequeña (más Lounge Pequeño)": 1 if area <= 1000 else 0,
                "Grande (más Lounge Grande)": 1 if area >= 1000 else 0
            },
            "Individual": {
                "Pequeño (Quiet Room)": round_half_up(num_phonebooth(hotdesking, workers_number)*0.5),
                "Pequeño (Phonebooth)": round_half_up(num_phonebooth(hotdesking, workers_number)*0.5)
            },
            "Colaborativo":{
                "Pequeño": round_half_up(obs/4) if obs is not None else None,
                "Mediano": round_half_up(obs/9) if obs is not None else None,
                "Grande": round_half_up(obs/13) if obs is not None else None
            },
            "Coffee/Comedor":{
                "Mediano": 1 if (501 <= area <= 1500) else 0,
                "Grande": 1 if (area >= 1202) else 0
            },
            "Soporte":{
                "Kitchenette": 1 if area < 500 else 0,
                "Servidor Pequeño": 1 if area < 500 else 0,
                "Servidor Mediano": 1 if (501 <= area <= 1500) else 0,
                "Servidor Grande": 1 if area > 1501 else 0,
                "Baño Accesibilidad": 1 if area > 500 else 0,
                "Print Pequeño": round_half_up(1 + (area/600)),
                "Print Grande": round_half_up(area/1200)
            }
        }
        quantity = quantity_switcher[category_name][subcategory['name']]
        
    obs = int(round_half_up(obs)) if obs is not None else None

    return int(quantity), obs

def token_required(f):  
    @wraps(f)  
    def decorator(*args, **kwargs):

        bearer_token = request.headers.get('Authorization', None)
        try:
            token = bearer_token.split(" ")[1]
        except Exception as ierr:
            app.logger.error(ierr)
            abort(jsonify({'message': 'a valid bearer token is missing'}), 500)

        if not token:
            app.logger.debug("token_required")
            return jsonify({'message': 'a valid token is missing'})

        app.logger.debug("Token: " + token)
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'],
                              algorithms=['RS256'], audience="1")
            user_id: int = data['user_id']
            request.environ['user_id'] = user_id
        except Exception as err:
            return jsonify({'message': 'token is invalid', 'error': err})
        except KeyError as kerr:
            return jsonify({'message': 'Can\'t find user_id in token', 'error': kerr})

        return f(*args, **kwargs)

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
          required:
            - hotdesking_level
            - collaboration_level
            - num_of_workers
          properties:
            hotdesking_level:
                type: number
                description: Hotdesking level
            collaboration_level:
                type: number
                description: Collaboration Level
            num_of_workers:
                type: integer
                description: num of workers
        responses:
          201:
            description: "Area value"
          500:
            description: "Server error"
    """
    if not request.json or (not 'hotdesking_level' and not 'collaboration_level' and not 'num_of_workers') in request.json:
        abort(400)
    
    try:
        hotdesking_level = request.json['hotdesking_level']
        collaboration_level = request.json['collaboration_level']
        workers_num = request.json['num_of_workers']

        area = area_calc(hotdesking_level, collaboration_level, workers_num)

        if(area):
            return jsonify({'area': area}), 200

        return jsonify({'message': "Error, the area could not be calculated. Try again."}), 500
    
    except Exception as exp:
        app.logger.error(f"Error in database: mesg ->{exp}")
        return exp, 500

@app.route('/api/m2/generate', methods = ['POST'])
@token_required
def generate_workspaces():
    """
        Get generated workspaces
        ---
        produces:
        - "application/json"
        parameters:
        - in: "body"
          name: "body"
          description: "Data required for workspaces to be generated"
          required: true
        responses:
          201:
            description: "Worskpaces data"
          400:
            description: "Missing data in the body"
          500:
            description: "Server error"
    """
    if not request.json or (not 'hotdesking_level' and not 'colaboration_level' and not 'num_of_workers' and not 'area') in request.json:
        abort(400)
        
    try:
        token = request.headers.get('Authorization', None)
        headers = {'Authorization': token}
        api_url = 'http://'+ SPACES_MODULE_HOST + ':' + str(SPACES_MODULE_PORT) + SPACES_MODULE_API_CREATE
        rv = requests.get(api_url, headers=headers)
        workspaces = json.loads(rv.text)
        data = request.json
        hotdesking_level = data['hotdesking_level']
        grade_of_collaboration = data['colaboration_level']
        workers_number = data['num_of_workers']
        area = data['area']

        for category in workspaces:
            category_name = category["name"]
            for subcategory in category["subcategories"]:
                quantity, obs = obs_and_quantity_calculator(category_name, subcategory, hotdesking_level, grade_of_collaboration, workers_number, area)
                subcategory['quantity'] = quantity
                subcategory['observation'] = obs
        data['workspaces'] = workspaces
        return jsonify(data), 200
    except requests.exceptions.RequestException as exp:
        app.logger.error(f"Connection error: ->{exp}")
        return exp, 500

if __name__ == '__main__':
    app.run(host= APP_HOST, port = APP_PORT, debug = True)