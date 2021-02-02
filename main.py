import jwt
import requests
import json
import math
import pprint
from lib import app, os, db, abort, jsonify, request, num_private_office, total_open_plan, num_formal_collaborative, num_informal_collaborative, num_phonebooth, area_calc, M2InternalConfigVar
from flask_swagger import swagger
from flask_swagger_ui import get_swaggerui_blueprint
from functools import wraps
from flask_cors import CORS
from sqlalchemy import UniqueConstraint
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.exc import SQLAlchemyError

# Loading Config Parameters
APP_HOST = os.getenv('APP_HOST', '127.0.0.1')
APP_PORT = os.getenv('APP_PORT', 5001)
SPACES_MODULE_HOST = os.getenv('SPACES_MODULE_IP', '127.0.0.1')
SPACES_MODULE_PORT = os.getenv('SPACES_MODULE_PORT', 5002)
SPACES_MODULE_API_CREATE = os.getenv('SPACES_MODULE_API_CREATE', '/api/spaces/create')

PRICES_MODULE_HOST = os.getenv('PRICES_MODULE_IP', '127.0.0.1')
PRICES_MODULE_PORT = os.getenv('PRICES_MODULE_PORT', 5008)
PRICES_MODULE_API = os.getenv('PRICES_MODULE_API', '/api/prices/')
PRICES_URL = f"http://{PRICES_MODULE_HOST}:{PRICES_MODULE_PORT}"

PROJECTS_MODULE_HOST = os.getenv('PROJECTS_MODULE_HOST', '127.0.0.1')
PROJECTS_MODULE_PORT = os.getenv('PROJECTS_MODULE_PORT', 5000)
PROJECTS_MODULE_API = os.getenv('PROJECTS_MODULE_API', '/api/projects/')
PROJECTS_URL = f"http://{PROJECTS_MODULE_HOST}:{PROJECTS_MODULE_PORT}"

CORS(app)

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
    collaboration_level: Value of the Collaborative Level
    workers_number: Value of Workers number
    area: Value of calculated Area
    density: Area density value
    """
    id = db.Column(db.Integer, primary_key=True)
    hot_desking_level = db.Column(db.Integer, nullable=False)
    collaboration_level = db.Column(db.Integer, nullable=False)
    workers_number = db.Column(db.Integer, nullable=False)
    area = db.Column(db.Float, nullable=False)
    density = db.Column(db.Float, nullable=False)
    project_id = db.Column(db.Integer, nullable=False, unique=True)
    workspaces = db.relationship(
        "M2GeneratedWorkspace",
        backref="m2_generated",
        cascade="all, delete, delete-orphan")

    def to_dict(self):
        """
        Convert to dictionary
        """

        workspaces_dicts = [workspace.to_dict()
                                for workspace in self.workspaces]
        dict = {
            'id': self.id,
            'hot_desking_level': self.hot_desking_level,
            'collaboration_level': self.collaboration_level,
            'workers_number': self.workers_number,
            'area': self.area,
            'density': self.density,
            'project_id': self.project_id,
            'workspaces': workspaces_dicts
        }
        return dict

    def serialize(self):
        """
        Serialize to json
        """
        return jsonify(self.to_dict())

class M2GeneratedWorkspace(db.Model):
    """
    M2GeneratedWorkspace.
    Represents the values of quantity and observation per space configured by the user 
    or previusly generated. All this according to the m2 value.

    Attributes
    ----------
    id: Represent the unique id of a M2 generated
    observation: Value of observation
    quantity: Value of quantity associated to space
    m2_gen_id: Foreign key of m2_gens associated
    space_id: Foreign key of space associated
    """
    __table_args__ = (db.UniqueConstraint('space_id', 'm2_gen_id'),)

    id = db.Column(db.Integer, primary_key=True)
    observation = db.Column(db.Integer)
    quantity = db.Column(db.Integer, nullable=False)
    space_id = db.Column(db.Integer, nullable=False)
    m2_gen_id = db.Column(db.Integer, db.ForeignKey(
        'm2_generated.id'), nullable=False)

    def to_dict(self):
        """
        Convert to dictionary
        """

        dict = {
            'id': self.id,
            'observation': self.observation,
            'quantity': self.quantity,
            'space_id': self.space_id,
            'm2_gen_id': self.m2_gen_id
        }
        return dict

    def serialize(self):
        """
        Serialize to json
        """
        return jsonify(self.to_dict())

db.create_all()
    
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
    if(category_name == "Area Soporte Reuniones Informales"):
        obs_switcher = {
          "Pequeño": num_informal_collaborative(hotdesking, grade_of_collaboration, workers_number)*0.2,
          "Mediano": num_informal_collaborative(hotdesking, grade_of_collaboration, workers_number)*0.3,
          "Grande": num_informal_collaborative(hotdesking, grade_of_collaboration, workers_number)*0.5
        }
        obs = obs_switcher[subcategory['name']]
    elif(category_name == "Sala Reunión"):
        obs = num_formal_collaborative(hotdesking, grade_of_collaboration, workers_number) * subcategory['usage_percentage']
    else:
        obs = None

    if(category_name == "Puestos Trabajo"):
        quantity = round_half_up(total_open_plan(hotdesking, workers_number))
    elif(category_name == "Area Servicios" and subcategory['name'] == "Baños"):
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
    elif(category_name == "Especiales"):
        quantity = 0
    else:
        quantity_switcher = {
            "Puestos Trabajo Privado":{
                "Privado Pequeño": round_half_up(num_private_office(hotdesking, workers_number)*0.7),
                "Privado Grande": round_half_up(num_private_office(hotdesking, workers_number)*0.3)
            },
            "Area Soporte":{
                "Recepción Pequeña (más Lounge Pequeño)": 1 if area <= 1000 else 0,
                "Recepción Grande (más Lounge Grande)": 1 if area >= 1000 else 0,
                "Quiet Room": round_half_up(num_phonebooth(hotdesking, workers_number)*0.5),
                "Phonebooth": round_half_up(num_phonebooth(hotdesking, workers_number)*0.5),
                "Workcoffee/Comedor Mediano": 1 if (501 <= area <= 1500) else 0,
                "Workcoffee/Comedor Grande": 1 if (area >= 1202) else 0,
                "Guardado Simple Bajo": 0,
                "Guardado Simple Alto": 0,
                "Locker": 0
            },
            "Area Soporte Reuniones Informales":{
                "Pequeño": round_half_up(obs/4) if obs is not None else None,
                "Mediano": round_half_up(obs/9) if obs is not None else None,
                "Grande": round_half_up(obs/13) if obs is not None else None
            },
            "Area Servicios":{
                "Kitchenette": 1 if area < 500 else 0,
                "Servidor 1 Gabinete": 1 if area < 500 else 0,
                "Servidor 2 Gabinetes": 1 if (501 <= area <= 1500) else 0,
                "Servidor 3 Gabinetes": 1 if area > 1501 else 0,
                "Baño Accesibilidad Universal": 1 if area > 500 else 0,
                "Print Pequeño": round_half_up(1 + (area/600)),
                "Print Grande": round_half_up(area/1200),
                "Sala Lactancia": 0,
                "Bodega": 0,
                "Coffee point": 0
            }
        }
        quantity = quantity_switcher[category_name][subcategory['name']]
        
    obs = int(round_half_up(obs)) if obs is not None else None

    return int(quantity), obs

def get_project_by_id(project_id, token):
    headers = {'Authorization': token}
    api_url = PROJECTS_URL + PROJECTS_MODULE_API + str(project_id)
    rv = requests.get(api_url, headers=headers)
    if rv.status_code == 200:
        return json.loads(rv.text)
    elif rv.status_code == 500:
      raise Exception("Cannot connect to the projects module")
    return None

def exists_price_project_by_id(project_id, token):
    headers = {'Authorization': token}
    api_url = PRICES_URL + PRICES_MODULE_API + '/exists/' + str(project_id)
    rv = requests.get(api_url, headers=headers)
    if rv.status_code == 200:
        return json.loads(rv.text)
    elif rv.status_code == 500:
      raise Exception("Cannot connect to the prices module")
    return None

def update_prices_project_by_id(project_id, area, token):
  data={'m2':area}
  headers = {'Authorization': token}
  api_url = PRICES_URL + PRICES_MODULE + '/update/' + str(project_id)
  rv = requests.put(api_url, json=data, headers=headers)
  if rv.status_code == 200:
    return json.loads(rv.text)
  elif rv.status_code == 500:
    raise Exception("Cannot connect to the prices module")
  return None

def update_project_by_id(project_id, data, token):
  headers = {'Authorization': token}
  api_url = PROJECTS_URL + PROJECTS_MODULE_API + str(project_id)
  rv = requests.put(api_url, json=data, headers=headers)
  if rv.status_code == 200:
    return json.loads(rv.text)
  elif rv.status_code == 500:
    raise Exception("Cannot connect to the projects module")
  return None

def token_required(f):  
    @wraps(f)  
    def decorator(*args, **kwargs):

        bearer_token = request.headers.get('Authorization', None)
        try:
            token = bearer_token.split(" ")[1]
        except Exception as ierr:
            app.logger.error(ierr)
            return jsonify({'message': 'a valid bearer token is missing'}), 500

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
        Get M2 area
        ---
        produces:
        - "application/json"
        tags:
        - "M2"
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
    if request.json.keys() != {'hotdesking_level','collaboration_level','num_of_workers'}:
        return f'Missing data in the body request', 400
    
    try:
        hotdesking_level = request.json['hotdesking_level']
        collaboration_level = request.json['collaboration_level']
        workers_num = request.json['num_of_workers']

        area = area_calc(hotdesking_level, collaboration_level, workers_num)

        if(area):
            return jsonify({'area': area}), 200

        return jsonify({'message': "Error, the area could not be calculated. Try again."}), 500
    
    except Exception as exp:
        msg = f"Error: mesg ->{exp}"
        app.logger.error(msg)
        return msg, 500

@app.route('/api/m2/generate', methods = ['POST'])
@token_required
def generate_workspaces():
    """
        Get generated M2 data and workspaces
        ---
        produces:
        - "application/json"
        tags:
        - "M2"
        parameters:
        - in: "body"
          name: "body"
          description: "Data required for M2 data and workspaces to be generated"
          required:
            - area
            - hotdesking_level
            - collaboration_level
            - num_of_workers
          properties:
            area:
              type: number
              description: Area value previously calculated
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
            description: "Generated M2 data and worskpaces"
          400:
            description: "Missing data in the request body"
          500:
            description: "Server error"
    """
    if request.json.keys() != {'area','hotdesking_level','collaboration_level','num_of_workers'}:
        return f'Missing data in the request body', 400
        
    try:
        token = request.headers.get('Authorization', None)
        headers = {'Authorization': token}
        api_url = 'http://'+ SPACES_MODULE_HOST + ':' + str(SPACES_MODULE_PORT) + SPACES_MODULE_API_CREATE
        rv = requests.get(api_url, headers=headers)
        workspaces = json.loads(rv.text)
        data = request.json
        hotdesking_level = data['hotdesking_level']
        grade_of_collaboration = data['collaboration_level']
        workers_number = data['num_of_workers']
        area = data['area']

        for category in workspaces:
            category_name = category["name"]
            category["subcategories"][:] = [subcategory for subcategory in category["subcategories"] if len(subcategory['spaces']) > 0]
            for subcategory in category["subcategories"]:
              for space in subcategory['spaces']:
                space['quantity'] = 0
              quantity, obs = obs_and_quantity_calculator(category_name, subcategory, hotdesking_level, grade_of_collaboration, workers_number, area)
              subcategory['spaces'][0]['quantity'] = quantity
              subcategory['observation'] = obs
        data['workspaces'] = workspaces
        return jsonify(data), 200
    except requests.exceptions.RequestException as exp:
        msg = f"Connection error: ->{exp}"
        app.logger.error(msg)
        return msg, 500

@app.route('/api/m2/save', methods = ['POST'])
@token_required
def save_workspaces():
    """
        Save generated M2 data and workspaces
        ---
        produces:
        - "application/json"
        tags:
        - "M2"
        parameters:
        - in: "body"
          name: "body"
          description: "Workspaces thats includes Category and Subcategory with full info., and Spaces with ID value. 
          Each Space (or Workspace) have a quantity setted by user in the current project."
          required:
            - project_id
            - area
            - hotdesking_level
            - collaboration_level
            - num_of_workers
            - workspaces
          properties:
            project_id:
              type: integer
              description: ID of the current project
            area:
              type: number
              description: Area value previously calculated
            hotdesking_level:
              type: number
              description: Hotdesking level
            collaboration_level:
              type: number
              description: Collaboration Level
            num_of_workers:
              type: integer
              description: num of workers
            workspaces:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                  name:
                    type: string
                  subcategories:
                    type: array
                    items:
                      type: object
                      properties:
                        id:
                          type: integer
                        area:
                          type: number
                        category_id:
                          type: integer    
                        name:
                          type: string
                        observation:
                          type: integer
                        people_capacity:
                          type: number
                        unit_area:
                          type: number
                        usage_percentage:
                          type: number
                        spaces:
                          type: array
                          items:
                            type: object
                            properties:
                              id:
                                type: integer
                              quantity:
                                type: integer
        responses:
          201:
            description: "M2 Worskpaces data with the current Project info."
          400:
            description: "Missing data in the body"
          500:
            description: "Server error"
    """
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(data)
    if request.is_json:
        data = request.json
        pp.pprint(data['project_id'])
        token = request.headers.get('Authorization', None)
        pp.pprint(token)
        print('hola')
        try:
            print('hola1')
            project = get_project_by_id(data['project_id'], token)
            
            if(project is not None):
                print('hola3')
                m2_gen = M2Generated.query.filter_by(project_id=project['id']).first()
                if m2_gen is not None:
                    db.session.delete(m2_gen)
                    db.session.commit()
                m2_gen = M2Generated()
                m2_gen.hot_desking_level = data['hotdesking_level']
                m2_gen.collaboration_level = data['collaboration_level']
                m2_gen.workers_number = data['num_of_workers']
                m2_gen.area = data['area']
                m2_gen.density = data['area']/data['num_of_workers']
                m2_gen.project_id = data['project_id']

                for category in data['workspaces']:
                  for subcategory in category['subcategories']:
                    for space in subcategory['spaces']:
                      m2_gen_workspace = M2GeneratedWorkspace()
                      m2_gen_workspace.quantity = space['quantity']
                      m2_gen_workspace.observation = subcategory['observation']
                      m2_gen_workspace.space_id = space['id']
                      m2_gen.workspaces.append(m2_gen_workspace)

                db.session.add(m2_gen)
                db.session.commit()
                pp.pprint(m2_gen)
                project = update_project_by_id(data['project_id'], {'m2_gen_id': m2_gen.id}, token)
                pp.pprint(project)
                if project is not None:
                  project['m2_generated_data'] = m2_gen.to_dict()
                  return jsonify(project), 201
                return "Cannot update the Project because doesn't exist", 404    
                
                prices_project = exists_price_project_by_id(data['project_id'],token) 
                pp.pprint(prices_project['status'])
                if prices_project['status'] == 'Yes':
                  prices_project = update_prices_project_by_id(data['project_id'],data['area'],token)
                  pp.pprint(prices_project)

            else:
                return "Project doesn't exist or the id is not included on the body", 404
        except SQLAlchemyError as e:
            db.session.rollback()
            return f'Error saving data: {e}', 500
        except Exception as exp:
            msg = f"Error: mesg ->{exp}"
            app.logger.error(msg)
            return msg, 500
    else:
        return 'Body isn\'t application/json', 400

@app.route('/api/m2/<project_id>', methods = ['GET'])
@token_required
def get_m2_config_by_project_id(project_id):
    """
        Get latest configuration of M2 data and workspaces by current Project ID.
        ---
        parameters:
          - in: path
            name: project_id
            type: integer
            description: Project ID
        tags:
        - "M2"
        responses:
          200:
            description: M2 data and workspaces Object.
          404:
            description: Project Not Found or the Proyect doesn't have a M2 configuration created.
          500:
            description: "Database error"
    """
    try:
        token = request.headers.get('Authorization', None)
        project = get_project_by_id(project_id, token)
        if(project is not None):
            m2_config = M2Generated.query.filter_by(project_id=project_id).first()
            if m2_config is not None:
                project['m2_generated_data'] = m2_config.to_dict()
                return jsonify(project), 200
            else:
                raise Exception("This Project doesn't have a workspaces configuration created")
        
        raise Exception("Project doesn't exist")
    except SQLAlchemyError as e:
      return f'Error getting data: {e}', 500
    except Exception as exp:
      msg = f"Error: mesg ->{exp}"
      app.logger.error(msg)
      return msg, 404

@app.route('/api/m2/constants', methods = ['GET'])
@token_required
def get_all_constants():
    """
        Get all M2 constants
        ---
        tags:
        - "M2/Constants"
        responses:
          200:
            description: List of constants used to calculate M2 area. 
          500:
            description: "Database error"
    """
    try:
        constants =  [c.to_dict() for c in M2InternalConfigVar.query.all()]
        return jsonify(constants), 200
    except SQLAlchemyError as e:
        return f'Error getting data: {e}', 500

@app.route('/api/m2/constants', methods = ['PUT'])
@token_required
def update_constants():
    """
        Update M2 constants
        ---
        produces:
        - "application/json"
        tags:
        - "M2/Constants"
        parameters:
        - in: "body"
          name: "body"
          description: "List of constants data to be updated."
          schema:
            type: array
            items:
              type: object
              properties:
                id: 
                  type: integer
                value:
                  type: number
        responses:
          200:
            description: List of constants used to calculate M2 area. 
          400:
            description: Body isn't application/json or empty body data.
          500:
            description: "Database error"
    """
    if request.is_json:
        if len(request.json) > 0:
            try:
                db.session.bulk_update_mappings(M2InternalConfigVar, request.json)
                db.session.commit()
                updated_constants =  [c.to_dict() for c in M2InternalConfigVar.query.all()]
                return jsonify(updated_constants), 200
            except SQLAlchemyError as e:
                return f'Error getting data: {e}', 500
        else:
            return 'Body data required', 400
    else:
        return 'Body isn\'t application/json', 400


if __name__ == '__main__':
    app.run(host= APP_HOST, port = APP_PORT, debug = True)