from flask import Flask, jsonify, abort, request
from flask_sqlalchemy import SQLAlchemy
import constants
import logging

import os

# Loading Config Parameters
DB_USER = os.getenv('DB_USER', 'wys')
DB_PASS = os.getenv('DB_PASSWORD', 'rac3e/07')
DB_IP = os.getenv('DB_IP_ADDRESS', '10.2.14.195')
DB_PORT = os.getenv('DB_PORT', '3307')
DB_SCHEMA = os.getenv('DB_SCHEMA', 'wys')

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql://{DB_USER}:{DB_PASS}@{DB_IP}:{DB_PORT}/{DB_SCHEMA}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.logger.setLevel(logging.DEBUG)
db = SQLAlchemy(app)

class M2InternalConfigVar(db.Model):
    """
    M2InternalConfigVar.
    Represent a configuration variable that are used to calc the final area.

    Attributes
    ----------
    id: Represent the unique id of a Internal SubCategory
    name: Name of a Internal Category
    value: Value of the variable
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120))
    value = db.Column(db.Float)

    def to_dict(self):
        """
        Convert to dictionary
        """

        dict = {
            'id': self.id,
            'name': self.name,
            'value': self.value
        }
        return dict

    def serialize(self):
        """
        Serialize to json
        """
        return jsonify(self.to_dict())

db.create_all()  # Create all tables

def load_config_vars():
    """
    Load all config vars by default defined in constants.py
    If variable exist, don't change
    """

    total_rows = db.session \
        .query(M2InternalConfigVar) \
        .count()

    # If there are variables in database, do nothing
    if total_rows > 0:
        return

    # Else put the variables by defect

    try:
        for k, v in constants.GLOBAL_CONFIG_VARS.items():
            db.session.add(M2InternalConfigVar(name=k, value=v))
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"load_config_vars -> {e}")


load_config_vars()


def m2_open_plan(hotdesking, workers_number):
    """
    Calc the area in m2 for open plan
    :param hotdesking: Integer number between 70 and 100
    :param workers_number: Integer number between 0 to 1000
    :return: area in m2 for open plan spaces
    """
    try:
        op_density = M2InternalConfigVar.query \
            .filter_by(name=constants.DEN_PUESTO_TRABAJO_OPEN) \
            .first() \
            .value
        m2 = total_open_plan(hotdesking, workers_number) * float(op_density)
        return m2

    except Exception as e:
        app.logger.error(f"calc_open_plan -> Message: {e}")
        raise e


def total_open_plan(hotdesking, workers_number):
    """
    Calc the total open plan desks
    :param hotdesking: Integer number between 70 and 100
    :param workers_number: Integer number between 0 to 1000
    :return: Total Open Plan Desks
    """
    try:
        open_plan_factor = M2InternalConfigVar.query \
            .filter_by(name=constants.FACTOR_OPEN_PLAN) \
            .first() \
            .value
        return open_plan_factor * total_individual_spaces(hotdesking, workers_number)
    except Exception as e:
        app.logger.error(f"calc_total_open_plan -> Message: {e}")
        raise e


def total_individual_spaces(hotdesking, workers_number):
    """
    Calc the number of the total individul desks given hotdesking level and number of workers
    :param hotdesking: Integer number between 70 and 100
    :param workers_number: Integer number between 0 to 1000
    :return: the number of total individual desks according to the given parameters
    """
    return hotdesking * workers_number / 100.0


def factor_private_office(hotdesking):
    """
    Calc the factor private office parameter
    :param hotdesking: Integer number between 70 and 100
    :return: A factor that is used to calc the number of private office
    """

    if hotdesking < 70:
        factor = 0.0

    elif 70 <= hotdesking < 85:
        factor = 0.05
    else:
        factor = 0.1

    return factor


def num_private_office(hotdesking, workers_number):
    """
    Calc the num of private office given hotdesking
    :param hotdesking: Integer number between 70 and 100
    :param workers_number: Integer number between 0 to 1000
    :return: Num of private office (float)
    """
    return factor_private_office(hotdesking) * total_individual_spaces(hotdesking, workers_number)


def m2_private_office(hotdesking, workers_number):
    """
    Calc the total area used by private offices
    :param hotdesking: Integer number between 70 and 100
    :param workers_number: Integer number between 0 to 1000
    :return: The total area used by private offices
    """
    try:
        po_density = M2InternalConfigVar.query \
            .filter_by(name=constants.DEN_OFICINA_PRIVADA) \
            .first() \
            .value

        return po_density * num_private_office(hotdesking, workers_number)

    except Exception as e:
        app.logger.error(f"private_office_m2 -> Message: {e}")
        raise e


def factor_phonebooth(hotdesking):
    """
    Calc the factor phonebooth that helps to calc the number of
    phonebooths
    :param hotdesking: Integer number between 70 and 100
    :return: The factor phonebooth (Float)
    """
    try:
        po_factor = factor_private_office(hotdesking)
        op_factor = M2InternalConfigVar.query \
            .filter_by(name=constants.FACTOR_OPEN_PLAN) \
            .first() \
            .value
        return 1 - po_factor - op_factor
    except Exception as e:
        app.logger.error(f"factor_phonebooth -> Message: {e}")
        raise e


def num_phonebooth(hotdesking, workers_number):
    """
    Calc the quantity of phonebooth needed
    :param hotdesking: Integer number between 70 and 100
    :param workers_number: Integer number between 0 to 1000
    :return: The number of phonebooth needed
    """
    try:
        return factor_phonebooth(hotdesking) * total_individual_spaces(hotdesking, workers_number)
    except Exception as e:
        app.logger.error(f"num_phonebooth -> Message: {e}")
        raise e


def m2_phonebooth(hotdesking, workers_number):
    """
    Calc the area in m2 that is needed of phonebooth spaces
    given hotdesking level and the number of workers.

    :param hotdesking: Integer number between 70 and 100
    :param workers_number: Integer number between 0 to 1000
    :return: Total phonebooth area.
    """
    try:
        pb_density = M2InternalConfigVar.query \
            .filter_by(name=constants.DEN_PHONEBOOTH) \
            .first() \
            .value
        return num_phonebooth(hotdesking, workers_number) * pb_density
    except Exception as e:
        app.logger.error(f"m2_phonebooth -> Message: {e}")
        raise e


def collaborative_spaces(hotdesking, grade_of_collaboration, workers_number):
    """
    Calc the total of collaborative spaces

    :param grade_of_collaboration: Integer between 30 and 50
    :param hotdesking: Integer number between 70 and 100
    :param workers_number: Integer number between 0 to 1000
    :return number of total of collaborative spaces
    """
    num_ind_spaces = total_individual_spaces(hotdesking=hotdesking, workers_number=workers_number)
    return (grade_of_collaboration * num_ind_spaces * 1.0)/(100.0 - grade_of_collaboration)


def factor_formal_collaborative(grade_of_collaboration):
    """
    Calc the formal collaborative factor
    :param grade_of_collaboration: Integer between 30 and 50
    :return formal collaborative factor
    """
    if grade_of_collaboration < 37:
        return 0.9
    elif 37 <= grade_of_collaboration < 43:
        return 0.7
    else:
        return 0.5


def num_informal_collaborative(hotdesking, grade_of_collaboration, workers_number):
    """
    Calc the total of informal collaboratives spaces

    :param grade_of_collaboration: Integer between 30 and 50
    :param hotdesking: Integer number between 70 and 100
    :param workers_number: Integer number between 0 to 1000
    :return number of total informal collaborative spaces
    """
    num_col_spaces = collaborative_spaces(hotdesking, grade_of_collaboration, workers_number)
    return num_col_spaces * (1-factor_formal_collaborative(grade_of_collaboration))


def m2_informal_collaborative(hotdesking, grade_of_collaboration, workers_number):
    """
        Calc the total area of informal collaboratives spaces

        :param grade_of_collaboration: Integer between 30 and 50
        :param hotdesking: Integer number between 70 and 100
        :param workers_number: Integer number between 0 to 1000
        :return: total area informal collaborative spaces
    """
    num_inf_col = num_informal_collaborative(hotdesking, grade_of_collaboration, workers_number)
    try:
        ic_density = M2InternalConfigVar.query \
            .filter_by(name=constants.DEN_COLABORATIVO_INFORMAL) \
            .first() \
            .value
        return num_inf_col * ic_density

    except Exception as e:
        app.logger.error(f"m2_informal_collaborative -> Message: {e}")
        raise e


def num_formal_collaborative(hotdesking, grade_of_collaboration, workers_number):
    """
    Calc total of formal collaboratives spaces
    :param grade_of_collaboration: Integer between 30 and 50
    :param hotdesking: Integer number between 70 and 100
    :param workers_number: Integer number between 0 to 1000
    :return: total formal collaboratives spaces
    """
    ffc = factor_formal_collaborative(grade_of_collaboration)
    total_collaborative = collaborative_spaces(hotdesking, grade_of_collaboration, workers_number)
    return ffc * total_collaborative


def m2_formal_collaborative(hotdesking, grade_of_collaboration, workers_number):
    """
    Calc total area of formal collaboratives spaces
    :param grade_of_collaboration: Integer between 30 and 50
    :param hotdesking: Integer number between 70 and 100
    :param workers_number: Integer number between 0 to 1000
    :return: total area of formal collaboratives spaces
    """
    try:
        den_col_form = M2InternalConfigVar.query \
            .filter_by(name=constants.DEN_COLABORATIVO_FORMAL) \
            .first() \
            .value
        return den_col_form * num_formal_collaborative(hotdesking, grade_of_collaboration, workers_number)
    except Exception as e:
        app.logger.error(f"m2_informal_collaborative -> Message: {e}")
        raise e


def m2_support(hotdesking, workers_number):
    """
    Calc the total area of support spaces
    :param hotdesking: Integer number between 70 and 100
    :param workers_number: Integer number between 0 to 1000
    :return: total area of soporte spaces
    """
    try:
        private_office = m2_private_office(hotdesking, workers_number)
        open_plan = m2_open_plan(hotdesking, workers_number)
        den_support = M2InternalConfigVar.query \
            .filter_by(name=constants.DEN_SOPORTE) \
            .first() \
            .value
        use_percent = den_support / (100.0 - den_support)
        return (private_office + open_plan) * use_percent

    except Exception as e:
        app.logger.error(f"m2_soporte -> Message: {e}")
        raise e


def m2_circulations(hotdesking, workers_number):
    """
    Calc the total area of circulation spaces
    :param hotdesking: Integer number between 70 and 100
    :param workers_number: Integer number between 0 to 1000
    :return: total area of soporte spaces
    """
    try:
        private_office = m2_private_office(hotdesking, workers_number)
        open_plan = m2_open_plan(hotdesking, workers_number)
        den_circ = M2InternalConfigVar.query \
            .filter_by(name=constants.DEN_CIRCULACIONES) \
            .first() \
            .value
        use_percent = den_circ / (100.0 - den_circ)
    except Exception as e:
        app.logger.error(f"m2_circulations -> Message: {e}")
        raise e

    return (private_office + open_plan + m2_support(hotdesking, workers_number)) * use_percent


def area_calc(hotdesking, grade_of_collaboration, workers_number):
    """
    Calc the total area given hotdesking level, grade of collaboration and number of workers
    :param hotdesking: Integer number between 70 and 100
    :param grade_of_collaboration: Integer between 30 and 50
    :param workers_number: workers_number: Integer number between 0 to 1000
    :return: Total area needed
    """

    return m2_support(hotdesking, workers_number) + \
           m2_circulations(hotdesking, workers_number) + \
           m2_private_office(hotdesking, workers_number) + \
           m2_open_plan(hotdesking, workers_number) + \
           m2_phonebooth(hotdesking, workers_number) + \
           m2_formal_collaborative(hotdesking, grade_of_collaboration, workers_number) + \
           m2_informal_collaborative(hotdesking, grade_of_collaboration, workers_number)