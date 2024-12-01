import uuid
from storage import db
from sqlalchemy import event
from typing import Dict
from app import bcrypt
from datetime import datetime


class BaseModel:
    id = db.Column(db.String(60), primary_key=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.id = str(uuid.uuid4())

    def to_dict(self) -> Dict:
        model_dict = {}
        model = {column.name: getattr(self, column.name) for column in self.__table__.columns}
        for key, value in model.items():
            if key == 'created_at':
                model_dict['created_at'] = self.created_at.isoformat()
            elif key == 'updated_at':
                model_dict['updated_at'] = self.updated_at.isoformat()
            elif key == '_sa_instance_state' or key == 'password':
                continue
            else:
                model_dict[key] = value

        return model_dict


class User(BaseModel, db.Model):
    __tablename__ = 'user'
    email = db.Column(db.String(60), nullable=False, default=getenv('ADMIN_EMAIL'))
    password = db.Column(
        db.String(60),
        nullable=False,
        default=bcrypt.generate_password_hash(getenv('ADMIN_PWD')).decode('utf-8')
    )


class Project(BaseModel, db.Model):
    __tablename__ = 'projects'
    url = db.Column(db.String(256))
    image = db.Column(db.String(256))
    name = db.Column(db.String(60), nullable=False)
    description = db.Column(db.Text, nullable=False)


class Company(BaseModel, db.Model):
    __tablename__ = 'companies'
    name = db.Column(db.String(60), nullable=False)
    description = db.Column(db.Text, nullable=False)


class InvalidToken(BaseModel, db.Model):
    __tablename__ = 'invalid_tokens'
    jti = db.Column(db.String(36), nullable=False, index=True)

    @classmethod
    def verify_jti(cls, jti: str) -> bool:
        return bool(db.get(cls, jti=jti))


def delete_file(mapper, connection, target):
    import os
    from app_main import app

    if target.image:
        path = os.path.join(app.root_path, os.getenv('UPLOAD_DIR'), target.image)
        if os.path.exists(path):
            os.remove(path)

event.listen(Project, 'after_delete', delete_file)
