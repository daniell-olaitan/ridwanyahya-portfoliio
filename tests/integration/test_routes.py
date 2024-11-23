from exc import AbortException
from unittest.mock import patch, MagicMock
from tests.integration.base_test import BaseTestCase


class TestRoutes(BaseTestCase):
    """
    Test all the routes
    """

    def test_login_success(self):
        """
        Test the method that logs the user in
        """
        resp = self.test_client.post(
            '/login',
            data=self.login
        )

        self.assertEqual(resp.status_code, 200)
        self.assertIn('access_token', resp.get_json())

    def test_login_incorrect_input_field(self):
        """
        Test the method that logs the user in using an invalid email
        """
        resp = self.test_client.post(
            '/login',
            data={
                'name': '',
                'password': self.test_pwd
            }
        )

        self.assertEqual(resp.status_code, 422)

    def test_login_incorrect_password(self) -> None:
        """
        Test login method with incorrect password
        """
        resp = self.test_client.post(
            '/login',
            data={
                'email': self.test_email,
                'password': 'wrongpassword'
            }
        )

        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.get_json()['data'], {'error': 'invalid password'})

    def test_login_unregistered_email(self) -> None:
        """
        Test login method with unregistered email
        """
        resp = self.test_client.post(
            '/login',
            data={
                'email': 'unregistered_email',
                'password': self.test_pwd
            }
        )

        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.get_json()['data'], {'error': 'email not registerd'})

    def test_logout(self) -> None:
        """
        Test the log out route
        """
        auth_header = self.login_user()

        resp = self.test_client.get('/logout')

        self.assertEqual(resp.status_code, 401)
        self.assertEqual(resp.get_json(), {
            'status': 'fail',
            'data': {'token': 'missing access token'},
        })

        resp = self.test_client.get('/logout', headers=auth_header)

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json(), {
            'status': 'success',
            'data': {}
        })

        resp = self.test_client.get('/logout', headers=auth_header)

        self.assertEqual(resp.status_code, 401)
        self.assertEqual(resp.get_json(), {
            'status': 'fail',
            'data': {'token': 'token has been revoked'}
        })

    def test_change_password(self) -> None:
        """
        Test the change password route
        """
        auth_header = self.login_user()
        test_cases = [
            (self.test_pwd, 'newpassword', 200, {'message': 'password changed'}),
            ('wrongpassword', 'newpassword', 400, {'error': 'invalid password'}),
        ]

        for current_password, new_password, status, data in test_cases:
            with self.subTest():
                resp = self.test_client.post(
                    '/change-password',
                    headers=auth_header,
                    data={
                        'current_password': current_password,
                        'new_password': new_password
                    }
                )

                self.assertEqual(resp.status_code, status)
                self.assertEqual(resp.get_json()['data'], data)

    def test_change_password_invalid_input_field(self) -> None:
        auth_header = self.login_user()
        resp = self.test_client.post(
            '/change-password',
            headers=auth_header,
            data={
                'old_password': self.test_pwd,
                'new_password': 'newpassword'
            }
        )

        self.assertEqual(resp.status_code, 422)
        self.assertEqual(resp.get_json()['data'], {'error': 'invalid input'})

    @patch('storage.db.update')
    def test_change_password_database_error(self, update_mock: MagicMock) -> None:
        update_mock.side_effect = AbortException({'error':'object does not exist'}, 'Not Found', 404)
        auth_header = self.login_user()
        resp = self.test_client.post(
            '/change-password',
            headers=auth_header,
            data={
                'current_password': self.test_pwd,
                'new_password': 'newpassword'
            }
        )

        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp.get_json()['data'], {'error':'object does not exist'})

    def test_get_a_company(self) -> None:
        """
        Test the get a company route
        """
        company = self.create_company()
        resp = self.test_client.get(
            f'/companies/{company.id}',
        )

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json()['data']['name'], self.company_name)

    def test_get_a_company_not_found(self) -> None:
        """
        Test the get a company route
        """
        resp = self.test_client.get(
            f'/companies/{2}',
        )

        self.assertEqual(resp.status_code, 404)

    def test_get_a_project(self) -> None:
        """
        Test the get a company route
        """
        project = self.create_project()
        resp = self.test_client.get(
            f'/projects/{project.id}',
        )

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json()['data']['name'], self.project_name)

    def test_get_a_project_not_found(self) -> None:
        """
        Test the get a company route
        """
        resp = self.test_client.get(
            f'/projects/{2}',
        )

        self.assertEqual(resp.status_code, 404)

    def test_get_companies(self) -> None:
        companies = [self.create_company() for _ in range(2)]
        resp = self.test_client.get('/companies')

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.get_json()['data']), len(companies))
        self.assertEqual(type(resp.get_json()['data']), list)

    def test_get_companies_empty(self) -> None:
        resp = self.test_client.get('/companies')

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.get_json()['data']), 0)
        self.assertEqual(type(resp.get_json()['data']), list)

    def test_get_projects(self) -> None:
        projects = [self.create_project() for _ in range(2)]
        resp = self.test_client.get('/projects')

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.get_json()['data']), len(projects))
        self.assertEqual(type(resp.get_json()['data']), list)

    def test_get_projects_empty(self) -> None:
        resp = self.test_client.get('/projects')

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.get_json()['data']), 0)
        self.assertEqual(type(resp.get_json()['data']), list)

    def test_delete_company(self) -> None:
        auth_header = self.login_user()
        company = self.create_company()
        resp = self.test_client.delete(f"/companies/{company.id}", headers=auth_header)

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json()['data'], {})

    @patch('storage.db.delete')
    def test_delete_company_not_found(self, delete_mock: MagicMock) -> None:
        delete_mock.side_effect = AbortException({'error': 'object does not exist'}, 'Not Found', 404)
        auth_header = self.login_user()
        company = self.create_company()
        resp = self.test_client.delete(f"/companies/{company.id}", headers=auth_header)
        print(resp.data.decode())

        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp.get_json()['data'], {'error': 'object does not exist'})

    @patch('storage.db.delete')
    def test_delete_company_database_error(self, delete_mock: MagicMock) -> None:
        delete_mock.side_effect = AbortException({'error': 'error'})
        auth_header = self.login_user()
        company = self.create_company()
        resp = self.test_client.delete(f"/companies/{company.id}", headers=auth_header)

        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.get_json()['data'], {'error':'error'})
