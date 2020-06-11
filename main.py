from lib import app, db, abort, jsonify, request, area_calc
from flask_swagger import swagger
from flask_swagger_ui import get_swaggerui_blueprint
from functools import wraps

# Swagger Config

SWAGGER_URL = '/api/docs/'
API_URL = '/api/spec'
swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={  # Swagger UI config overrides
        'app_name': "WYS Api. Project Service"
    }
)

app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

@app.route("/api/spec", methods=['GET'])
def spec():
    return jsonify(swagger(app))

@app.route('/api/m2', methods = ['GET'])
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

        return jsonify({'message': "Error, it was possible to calculate the area. Try again."}), 500
    
    except Exception as exp:
        app.logger.error(f"Error in database: mesg ->{exp}")
        return exp, 500

if __name__ == '__main__':
    app.run()
    app.debug = True