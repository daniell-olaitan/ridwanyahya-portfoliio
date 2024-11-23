import unittest
from app import create_app
from storage import DBStorage
from exc import AbortException
from sqlalchemy.exc import IntegrityError
from unittest.mock import MagicMock, patch


class TestModel:
    """Mock model class for testing."""
    id = 1
    name = 'Test'
    created_at = '2024-11-22'

    def __init__(self, **fields):
        for key, value in fields.items():
            setattr(self, key, value)


class TestDBStorage(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app.app_context().push()
        self.storage = DBStorage()
        self.storage.session = MagicMock()
        self.model = TestModel

    def test_new_creates_instance(self):
        fields = {'name': 'Sample'}
        instance = self.storage.new(self.model, **fields)
        self.assertIsInstance(instance, TestModel)
        self.assertEqual(instance.name, 'Sample')

    def test_save_commits_instance(self):
        instance = TestModel(id=1)
        self.storage.session.get.return_value = instance
        saved_instance = self.storage.save(self.model, instance)

        self.storage.session.add.assert_called_once_with(instance)
        self.storage.session.commit.assert_called_once()
        self.assertEqual(saved_instance, instance)

    def test_save_raises_exception_on_integrity_error(self):
        self.storage.session.commit.side_effect = IntegrityError(None, None, None)
        instance = TestModel(id=1)

        with self.assertRaises(AbortException):
            self.storage.save(self.model, instance)
        self.storage.session.rollback.assert_called_once()

    def test_save_new_creates_and_saves_instance(self):
        fields = {'name': 'NewSample'}
        self.storage.session.get.return_value = TestModel(**fields)

        instance = self.storage.save_new(self.model, **fields)
        self.assertIsInstance(instance, TestModel)
        self.assertEqual(instance.name, 'NewSample')

    def test_delete_removes_instance(self):
        instance = TestModel(id=1)
        self.storage.session.get.return_value = instance

        self.storage.delete(self.model, 1)
        self.storage.session.delete.assert_called_once_with(instance)
        self.storage.session.commit.assert_called_once()

    def test_delete_raises_exception_for_nonexistent_object(self):
        self.storage.session.get.return_value = None

        with self.assertRaises(AbortException):
            self.storage.delete(self.model, 1)

    def test_update_updates_fields(self):
        instance = TestModel(id=1, name='OldName')
        self.storage.session.get.return_value = instance
        updated_fields = {'name': 'UpdatedName'}

        updated_instance = self.storage.update(self.model, 1, **updated_fields)

        self.assertEqual(updated_instance.name, 'UpdatedName')
        self.storage.session.commit.assert_called_once()

    @patch('app.bcrypt.generate_password_hash')
    def test_update_password_field(self, mock_bcrypt):
        mock_bcrypt.return_value.decode.return_value = 'hashed_password'
        instance = TestModel(id=1, password='old_password')
        self.storage.session.get.return_value = instance

        self.storage.update(self.model, 1, password='new_password')
        self.assertEqual(instance.password, 'hashed_password')

    def test_get_retrieves_instance(self):
        instance = TestModel(id=1)
        self.storage.session.query(self.model).filter_by.return_value.first.return_value = instance

        result = self.storage.get(self.model, id=1)
        self.assertEqual(result, instance)

    def test_get_some_retrieves_filtered_instances(self):
        instances = [TestModel(id=1), TestModel(id=2)]
        self.storage.session.query(self.model).filter_by.return_value.order_by.return_value.all.return_value = instances

        results = self.storage.get_some(self.model, name='Test')
        self.assertEqual(results, instances)

    def test_get_all_retrieves_all_instances(self):
        instances = [TestModel(id=1), TestModel(id=2)]
        self.storage.session.query(self.model).order_by.return_value.all.return_value = instances

        results = self.storage.get_all(self.model)
        self.assertEqual(results, instances)


if __name__ == '__main__':
    unittest.main()
