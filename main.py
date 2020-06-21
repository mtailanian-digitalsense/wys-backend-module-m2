import jwt
from lib import app, db, abort, jsonify, request, area_calc
from flask_swagger import swagger
from flask_swagger_ui import get_swaggerui_blueprint
from functools import wraps

try:
    f = open('oauth-public.key', 'r')
    key: str = f.read()
    f.close()
    app.config['SECRET_KEY'] = key
except Exception as e:
    app.logger.error(f'Can\'t read public key f{e}')
    exit(-1)

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

        return jsonify({'message': "Error, it was possible to calculate the area. Try again."}), 500
    
    except Exception as exp:
        app.logger.error(f"Error in database: mesg ->{exp}")
        return exp, 500

if __name__ == '__main__':
    app.run()
    app.debug = True