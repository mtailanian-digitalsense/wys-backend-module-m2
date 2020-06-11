import unittest
import os
import math
from unittest import TestCase

import constants
from main import M2InternalCategory, M2InternalSubCategory, \
    app, db, load_config_vars, M2InternalConfigVar, total_open_plan\
    ,open_plan_m2, num_private_office, private_office_m2, \
    factor_phonebooth, num_phonebooth, m2_phonebooth, collaborative_spaces,m2_informal_collaborative


class M2InternalCategoryTest(unittest.TestCase):
    NUM_SUB_CAT = 10

    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + \
                                                os.path.join('.', 'test.db')
        db.create_all()
        sub_cats = [
            M2InternalSubCategory(
                id=n,
                name=f"TEST{n}",
                category_id=n,
                density=float(f"{n}.{n}")) for n in range(self.NUM_SUB_CAT)]

        self.category = M2InternalCategory(name="TESTCAT1", id=1)

        for sub_cat in sub_cats:
            self.category.sub_categories.append(sub_cat)

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_to_dict(self):
        obj_dict = self.category.to_dict()
        assert len(obj_dict["sub_categories"]) == self.NUM_SUB_CAT


class M2ConfigVarsTest(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + \
                                                os.path.join('.', 'test.db')
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_load_config_vars(self):
        load_config_vars()
        total_rows = db.session \
            .query(M2InternalConfigVar) \
            .count()

        assert total_rows == len(constants.GLOBAL_CONFIG_VARS)

        load_config_vars()

        assert total_rows == len(constants.GLOBAL_CONFIG_VARS)


class M2LogicCalcTest(TestCase):
    def setUp(self):
        self.TOLERANCE = 0.0001
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + \
                                                os.path.join('.', 'test.db')
        db.create_all()
        load_config_vars()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_calc_total_open_plan(self):
        total = int(total_open_plan(hotdesking=100, workers_number=100))
        assert total == 90

        total = int(total_open_plan(hotdesking=70, workers_number=100))
        assert total == 63

        total = int(total_open_plan(hotdesking=86, workers_number=737))
        assert total == 570

    def test_calc_open_plan(self):
        m2 = open_plan_m2(hotdesking=100, workers_number=100)
        assert m2 == 293.4

        m2 = open_plan_m2(hotdesking=70, workers_number=100)
        assert m2 == 205.38

        m2 = open_plan_m2(hotdesking=86, workers_number=737)

        assert abs(m2 - 1859.62788) < self.TOLERANCE

    def test_num_private_office(self):
        total = int(round(num_private_office(100, 100)))
        assert total == 10

        total = int(round(num_private_office(70, 100)))
        assert total == 0.0

        total = int(round(num_private_office(86, 737)))
        assert total == 32

    def test_private_office_m2(self):
        m2 = private_office_m2(100, 100)
        assert abs(m2 - 119.3) < self.TOLERANCE

        m2 = private_office_m2(70, 100)
        assert abs(m2 - 0.0) < self.TOLERANCE

        m2 = private_office_m2(86, 737)
        assert abs(m2 - 378.0736300) < self.TOLERANCE

    def test_factor_phonebooth(self):
        factor = factor_phonebooth(100)
        assert abs(factor - 0.00) < self.TOLERANCE

        factor = factor_phonebooth(70)
        assert abs(factor - 0.1) < self.TOLERANCE

        factor = factor_phonebooth(86)
        assert abs(factor - 0.05) < self.TOLERANCE

    def test_num_phonebooth(self):
        num = int(round(num_phonebooth(100, 100)))
        assert abs(num - 0.00) < self.TOLERANCE

        num = int(round(num_phonebooth(70, 100)))
        assert abs(num - 7) < self.TOLERANCE

        num = int(round(num_phonebooth(86, 737)))
        assert abs(num - 32) < self.TOLERANCE

    def test_m2_phonebooth(self):
        m2 = m2_phonebooth(100, 100)
        assert abs(m2 - 0.00) < self.TOLERANCE

        m2 = m2_phonebooth(70, 100)
        assert abs(m2 - 21.28) < self.TOLERANCE

        m2 = m2_phonebooth(86, 737)
        assert abs(m2 - 96.3406400) < self.TOLERANCE

    def test_collaborative_spaces(self):
        num = int(round(collaborative_spaces(100, 50, 100)))
        assert num == 100

        num = int(round(collaborative_spaces(70, 30, 100)))
        assert num == 30

        num = int(round(collaborative_spaces(87, 40, 737)))
        assert num == 427

    def test_m2_informal_collaborative(self):
        m2 = m2_informal_collaborative(100, 50, 100)
        assert abs(m2 - 75.50) < self.TOLERANCE

        m2 = m2_informal_collaborative(70, 50, 100)
        assert abs(m2 - 52.85) < self.TOLERANCE

        m2 = m2_informal_collaborative(87, 40, 737)
        assert abs(m2 - 193.63938) < self.TOLERANCE


if __name__ == '__main__':
    unittest.main()
