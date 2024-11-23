import os
os.environ['CONFIG'] = 'testing'

import unittest
from auth import Auth
from models import User
from app import create_app
from exc import AbortException
from unittest.mock import patch, MagicMock


class TestAuth(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app.app_context().push()
        self.auth = Auth()
        self.user_data = {'email': 'test@example.com', 'password': 'hashedpassword'}
        self.user = MagicMock(spec=User)
        self.user.email = self.user_data['email']
        self.user.password = self.user_data['password']

    @patch('storage.db.get')
    @patch('app.bcrypt.check_password_hash')
    def test_authenticate_user_valid(self, mock_check_password_hash, mock_db_get):
        mock_db_get.return_value = self.user
        mock_check_password_hash.return_value = True

        authenticated_user = self.auth.authenticate_user('test@example.com', 'password')

        self.assertEqual(authenticated_user, self.user)
        mock_db_get.assert_called_once_with(User, email='test@example.com')
        mock_check_password_hash.assert_called_once_with(self.user.password, 'password')

    @patch('storage.db.get')
    @patch('app.bcrypt.check_password_hash')
    def test_authenticate_user_invalid_password(self, mock_check_password_hash, mock_db_get):
        mock_db_get.return_value = self.user
        mock_check_password_hash.return_value = False

        with self.assertRaises(AbortException) as context:
            self.auth.authenticate_user('test@example.com', 'wrongpassword')

        self.assertEqual(str(context.exception), "400 Bad Request: Bad Request")
        mock_db_get.assert_called_once_with(User, email='test@example.com')
        mock_check_password_hash.assert_called_once_with(self.user.password, 'wrongpassword')

    @patch('storage.db.get')
    def test_authenticate_user_email_not_registered(self, mock_db_get):
        mock_db_get.return_value = None

        with self.assertRaises(AbortException) as context:
            self.auth.authenticate_user('nonexistent@example.com', 'password')

        self.assertEqual(str(context.exception), "400 Bad Request: Bad Request")
        mock_db_get.assert_called_once_with(User, email='nonexistent@example.com')


if __name__ == '__main__':
    unittest.main()
