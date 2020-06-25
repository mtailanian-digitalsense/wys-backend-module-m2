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
        f = open('oauth-private.key', 'r')
        self.key = f.read()
        f.close()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    @staticmethod
    def build_token(key, user_id=1):
        payload = {
            "aud": "1",
            "jti": "450ca670aff83b220d8fd58d9584365614fceaf210c8db2cf4754864318b5a398cf625071993680d",
            "iat": 1592309117,
            "nbf": 1592309117,
            "exp": 1624225038,
            "sub": "23",
            "user_id": user_id,
            "scopes": [],
            "uid": 23
        }
        return ('Bearer ' + jwt.encode(payload, key, algorithm='RS256').decode('utf-8')).encode('utf-8')

    def test_get_m2_value(self):
        with app.test_client() as client:
            client.environ_base['HTTP_AUTHORIZATION'] = self.build_token(self.key)
            sent = {'hotdesking_level': 75, 'collaboration_level': 40, 'num_of_workers': 100}
            rv = client.post('/api/m2', data = json.dumps(sent), content_type='application/json')
            self.assertEqual(rv.status_code, 200)

    def test_get_generate_workspaces(self):
        with app.test_client() as client:
            client.environ_base['HTTP_AUTHORIZATION'] = self.build_token(self.key)
            sent = {'hotdesking_level': 75, 'collaboration_level': 40, 'num_of_workers': 100, 'area': 516.5305429864253}
            rv = client.post('/api/m2/generate', data = json.dumps(sent), content_type='application/json')
            self.assertEqual(rv.status_code, 200)

if __name__ == '__main__':
    unittest.main()