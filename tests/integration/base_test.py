import os
os.environ['CONFIG'] = 'testing'

import unittest
from storage import db
from app_main import app
from typing import TypeVar

Model = TypeVar('Model')


class BaseTestCase(unittest.TestCase):
    """
    Class for Base Test case that test cases can inherit from
    """

    @classmethod
    def setUpClass(cls) -> None:
        """
        Set up default values before the test
        """
        cls.db = db
        cls.app = app
        cls.app_context = cls.app.app_context()
        cls.test_client = cls.app.test_client()
        cls.test_email = 'oluwidaad@gmail.com'
        cls.test_pwd = 'admin123'
        cls.login = {
            'email': cls.test_email,
            'password': cls.test_pwd
        }

        cls.company_name = 'companyname'
        cls.company_description = 'companydescription'
        cls.project_name = 'projectname'
        cls.project_description = 'projectdescription'

    def setUp(self) -> None:
        """
        Set the app context and create the database
        """
        from models import User, Company, Project

        self.app_context.push()
        self.db.create_all()
        self.admin = db.get(User, email='oluwidaad@gmail.com')

        if not self.admin:
            self.admin = db.save_new(User)

        # self.company = db.save_new(
        #     Company,
        #     name=self.company_name,
        #     description=self.company_description
        # )

        # self.project = db.save_new(
        #     Company,
        #     name=self.company_name,
        #     description=self.company_description
        # )

    def tearDown(self) -> None:
        """
        Remove the app context and the database
        """
        self.db.session.remove()
        self.db.drop_all()
        self.app_context.pop()

    def login_user(self) -> dict:
        """
        Login the user
        """
        resp = self.test_client.post(
            '/login',
            data=self.login
        )

        access_token = resp.get_json()['access_token']
        auth_header = {
            'Authorization': f"Bearer {access_token}"
        }

        return auth_header

    def create_company(self) -> Model:
        from models import Company

        return db.save_new(
            Company,
            name=self.company_name,
            description=self.company_description
        )

    def create_project(self) -> Model:
        from models import Project

        return db.save_new(
            Project,
            name=self.project_name,
            description=self.project_description
        )
