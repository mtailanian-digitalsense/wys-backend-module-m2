import unittest
import os
import math
from unittest import TestCase

import constants
from lib import \
    app, db, load_config_vars, M2InternalConfigVar, total_open_plan, \
    m2_open_plan, num_private_office, m2_private_office, \
    factor_phonebooth, num_phonebooth, m2_phonebooth, collaborative_spaces, m2_informal_collaborative, \
    m2_formal_collaborative, m2_support, m2_circulations, area_calc

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
        self.TOLERANCE = 0.01
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
        m2 = m2_open_plan(hotdesking=100, workers_number=100)
        assert m2 == 293.4

        m2 = m2_open_plan(hotdesking=70, workers_number=100)
        assert m2 == 205.38

        m2 = m2_open_plan(hotdesking=86, workers_number=737)

        assert abs(m2 - 1859.62788) < self.TOLERANCE

    def test_num_private_office(self):
        total = int(round(num_private_office(100, 100)))
        assert total == 10

        total = int(round(num_private_office(70, 100)))
        assert total == 4.0

        total = int(round(num_private_office(86, 737)))
        assert total == 63

    def test_private_office_m2(self):
        m2 = m2_private_office(100, 100)
        assert abs(m2 - 91.00) < self.TOLERANCE

        m2 = m2_private_office(70, 100)
        assert abs(m2 - 31.85) < self.TOLERANCE

        m2 = m2_private_office(86, 737)
        assert abs(m2 - 576.78) < self.TOLERANCE

    def test_factor_phonebooth(self):
        factor = factor_phonebooth(100)
        assert abs(factor - 0.00) < self.TOLERANCE

        factor = factor_phonebooth(70)
        assert abs(factor - 0.05) < self.TOLERANCE

        factor = factor_phonebooth(86)
        assert abs(factor - 0.00) < self.TOLERANCE

    def test_num_phonebooth(self):
        num = int(round(num_phonebooth(100, 100)))
        assert abs(num - 0.00) < self.TOLERANCE

        num = int(round(num_phonebooth(70, 100)))
        assert abs(num - 3) < self.TOLERANCE

        num = int(round(num_phonebooth(86, 737)))
        assert abs(num - 0) < self.TOLERANCE

    def test_m2_phonebooth(self):
        m2 = m2_phonebooth(100, 100)
        assert abs(m2 - 0.00) < self.TOLERANCE

        m2 = m2_phonebooth(70, 100)
        assert abs(m2 - 10.64) < self.TOLERANCE

        m2 = m2_phonebooth(86, 737)
        assert abs(m2 - 0) < self.TOLERANCE

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

    def test_m2_formal_collaborative(self):
        m2 = m2_formal_collaborative(100, 50, 100)
        assert abs(m2 - 104.00) < self.TOLERANCE

        m2 = m2_formal_collaborative(70, 30, 100)
        assert abs(m2 - 56.16) < self.TOLERANCE

        m2 = m2_formal_collaborative(87, 40, 737)
        assert abs(m2 - 622.38176) < self.TOLERANCE

    def test_m2_support(self):
        m2 = m2_support(100, 100)
        assert abs(m2 - 67.84) < self.TOLERANCE

        m2 = m2_support(70, 100)
        assert abs(m2 - 41.86) < self.TOLERANCE

        m2 = m2_support(87, 737)
        assert abs(m2 - 434.95) < self.TOLERANCE

    def test_m2_circulations(self):
        m2 = m2_circulations(100, 100)
        assert abs(m2 - 243.51) < self.TOLERANCE

        m2 = m2_circulations(70, 100)
        assert abs(m2 - 150.28) < self.TOLERANCE

        m2 = m2_circulations(87, 737)
        assert abs(m2 - 1561.37) < self.TOLERANCE

    def test_area_calc(self):
        m2 = area_calc(100, 50, 100)
        assert abs(m2 - 875.25) < self.TOLERANCE

        m2 = area_calc(70, 30, 100)
        assert abs(m2 - 500.71) < self.TOLERANCE

        m2 = area_calc(87, 40, 737)
        assert abs(m2 - 5277.07880515837) < self.TOLERANCE


if __name__ == '__main__':
    unittest.main()
