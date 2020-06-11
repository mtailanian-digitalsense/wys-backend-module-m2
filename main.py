from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
import jwt
from flask_swagger import swagger
from flask_swagger_ui import get_swaggerui_blueprint
import constants

import os

# Loading Config Parameters
DB_USER = os.getenv('DB_USER', 'wys')
DB_PASS = os.getenv('DB_PASSWORD', 'rac3e/07')
DB_IP = os.getenv('DB_IP_ADDRESS', '10.2.19.195')
DB_PORT = os.getenv('DB_PORT', '3307')
DB_SCHEMA = os.getenv('DB_SCHEMA', 'wys')

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql://{DB_USER}:{DB_PASS}@{DB_IP}:{DB_PORT}/{DB_SCHEMA}"
db = SQLAlchemy(app)


class M2InternalCategory(db.Model):
    """
    M2InternalCategory.
    Represent a Internal Categories of Spaces that are used to calc the final area.

    Attributes
    ----------
    id: Represent the unique id of a Internal Category
    name: Name of a Internal Category
    subcategories: Subcategories associated to this category (One to Many)
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120))
    sub_categories = db.relationship(
        "M2InternalSubCategory",
        backref="m2_internal_category")

    def serialize(self):
        """
        Serialize to json
        """
        return jsonify(self.to_dict())

    def to_dict(self):
        """
        Convert to dictionary
        """

        sub_categories_dicts = [sub_category.to_dict()
                                for sub_category in self.sub_categories]

        obj_dict = {
            'id': self.id,
            'name': self.name,
            'sub_categories': sub_categories_dicts}

        return obj_dict


class M2InternalSubCategory(db.Model):
    """
    M2InternalSubCategories.
    Represent a Internal SubCategories of Spaces that are used to calc the final area.

    Attributes
    ----------
    id: Represent the unique id of a Internal SubCategory
    name: Name of a Internal Category
    category_id: Parent Category's ID (Many to One)
    """

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120))
    density = db.Column(db.Float)
    category_id = db.Column(db.Integer, db.ForeignKey(
        'm2_internal_category.id'), nullable=False)

    def serialize(self):
        """
        Serialize to json
        """
        return jsonify(self.to_dict())

    def to_dict(self):
        """
        Convert to dictionary
        """
        return {
            'id': self.id,
            'name': self.name,
            'density': self.density,
            'category_id': self.category_id
        }


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


def open_plan_m2(hotdesking, workers_number):
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

    if hotdesking < 80:
        factor = 0.0

    elif 80 <= hotdesking < 90:
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


def private_office_m2(hotdesking, workers_number):
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
        return 1-po_factor-op_factor
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
        return factor_phonebooth(hotdesking) * total_individual_spaces(hotdesking,workers_number)
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
