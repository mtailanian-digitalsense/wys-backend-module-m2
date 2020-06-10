import unittest
import os
import constants
from main import M2InternalCategory, M2InternalSubCategory, \
                 app, db,load_config_vars, M2InternalConfigVar



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



if __name__ == '__main__':
    unittest.main()
