from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
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

    total_rows = db.session\
                   .query(M2InternalConfigVar)\
                   .count()

    # If there are variables in database, do nothing
    if total_rows > 0:
        return

    # Else put the variables by defect

    try:
        for k,v in constants.GLOBAL_CONFIG_VARS.items():
            db.session.add(M2InternalConfigVar(name=k,value=v))
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"load_config_vars -> {e}")


load_config_vars()