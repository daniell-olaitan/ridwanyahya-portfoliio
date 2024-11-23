"""
Module for authentication
"""
import typing as t
from app import jwt
from storage import db
from flask import jsonify
from exc import AbortException
from flask.typing import ResponseReturnValue
from models import (
    User,
    InvalidToken
)

ModelType = t.TypeVar('Model')


@jwt.token_in_blocklist_loader
def check_if_token_is_blacklisted(
    jwt_header: t.Mapping[str, str],
    jwt_payload: t.Mapping[str, str]
) -> bool:
    """
    Check if user has logged out
    """
    jti = jwt_payload['jti']
    return InvalidToken.verify_jti(jti)


@jwt.expired_token_loader
def expired_token_callback(
    jwt_header: t.Mapping[str, str],
    jwt_payload: t.Mapping[str, str]
) -> ResponseReturnValue:
    """
    Check if access_token has expired
    """
    return jsonify({
        'status': 'fail',
        'data': {'token': 'token has expired'},
    }), 401


@jwt.revoked_token_loader
def revoked_token_callback(
    jwt_header: t.Mapping[str, str],
    jwt_payload: t.Mapping[str, str]
) -> ResponseReturnValue:
    """
    Check if access_token has been revoked
    """
    return jsonify({
        'status': 'fail',
        'data': {'token': 'token has been revoked'},
    }), 401


@jwt.unauthorized_loader
def unauthorized_callback(_) -> ResponseReturnValue:
    """
    Handle unauthorized access
    """
    return jsonify({
        'status': 'fail',
        'data': {'token': 'missing access token'},
    }), 401


class Auth:
    """
    Class for user authentication
    """
    def authenticate_user(self, email: str, password: str) -> User:
        """
        Validate user login details
        """
        from app import bcrypt

        user = db.get(User, email=email)
        if user:
            if bcrypt.check_password_hash(user.password, password):
                return user

            raise AbortException({'error': 'invalid password'})
        raise AbortException({'error': 'email not registerd'})
