from storage import db
from flask import Flask
from config import config
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager

bcrypt = Bcrypt()
jwt = JWTManager()


def create_app(app_env: str) -> Flask:
    app = Flask(__name__)
    app.url_map.strict_slashes = False
    app.config.from_object(config[app_env])

    db.init_app(app)
    jwt.init_app(app)
    bcrypt.init_app(app)
    CORS(app, resources={
        r'/*': {
            'origins': '*'
        }
    })

    with app.app_context():
        db.create_all()

    return app
