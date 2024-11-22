from flask_sqlalchemy import SQLAlchemy
from exc import AbortException
from sqlalchemy import desc
from sqlalchemy.exc import IntegrityError
from typing import (
    Type,
    Dict,
    List,
    TypeVar
)

Model = TypeVar('Model')

class DBStorage(SQLAlchemy):
    def new(self, model_type: Type[Model], **fields: Dict) -> Model:
        return model_type(**fields)

    def save(self, model_type: Type[Model], model: Model) -> Model:
        try:
            self.session.add(model)
            self.session.commit()

            return self.session.get(model_type, model.id)
        except IntegrityError as err:
            self.session.rollback()
            raise AbortException({'error': str(err).split('\n')[0]})

    def save_new(self, model_type: Type[Model], **fields: Dict) -> Model:
        model = self.new(model_type, **fields)
        return self.save(model_type, model)

    def delete(self, model_type: Type[Model], id: str) -> None:
        try:
            model = self.session.get(model_type, id)
            if not model:
                raise AbortException({'error':'object does not exist' }, 'Not Found', 404)

            self.session.delete(model)
            self.session.commit()
        except IntegrityError as err:
            self.session.rollback()
            raise AbortException({'error': str(err).split('\n')[0]})

    def update(self, model_type: Type[Model], id: str, **fields: Dict) -> Model:
        from app_main import bcrypt

        model = self.session.get(model_type, id)
        if not model:
            raise AbortException({'error':'object does not exist' }, 'Not Found', 404)

        for field, value in fields.items():
            if field == 'password':
                value = bcrypt.generate_password_hash(value).decode('utf-8')

            setattr(model, field, value)
            return self.save(model_type, model)

    def get(self, model_type: Type[Model], **fields: Dict) -> List[Model]:
        return self.session.query(model_type).filter_by(**fields).first()

    def get_some(self, model_type: Type[Model], **fields: Dict) -> List[Model]:
        return self.session.query(model_type).filter_by(**fields).order_by(desc(model_type.created_at)).all()

    def get_all(self, model_type: Type[Model]) -> List[Model]:
        return self.session.query(model_type).order_by(desc(model_type.created_at)).all()


db = DBStorage()
