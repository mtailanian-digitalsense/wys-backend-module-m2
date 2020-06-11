import unittest
import os
import json
import jwt
from main import app, db
from lib import load_config_vars

class MainTest(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + \
                                                os.path.join('.', 'test.db')
        db.create_all()
        load_config_vars()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_get_m2_value(self):
        with app.test_client() as client:
            sent = {'hotdesking_level': 75, 'colaboration_level': 40, 'num_of_workers': 100}
            rv = client.get('/api/m2', data = json.dumps(sent), content_type='application/json')
            self.assertEqual(rv.status_code, 200)

if __name__ == '__main__':
    unittest.main()