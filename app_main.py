from dotenv import load_dotenv
load_dotenv()

from os import getenv
from storage import db
from app import create_app
from exc import AbortException
from flask.typing import ResponseReturnValue
from flask import (
    abort,
    jsonify,
    request
)

from validations import (
    LoginSchema,
    ProjectSchema,
    CompanySchema,
    PasswordSchema,
    validate_input
)

app = create_app(getenv('CONFIG') or 'default')
with app.app_context():
    from models import User

    db.create_all()
    admin = db.get(User, email='oluwidaad@gmail.com')
    if not admin:
        admin = db.save_new(User)


# HTTP Error Handlers
@app.errorhandler(404)
def not_found(_: Exception) -> ResponseReturnValue:
    return jsonify({
        'status': 'fail',
        'data': {
            'error': 'not found'
        }
    }), 404


@app.errorhandler(422)
def invalid_input(_: Exception) -> ResponseReturnValue:
    return jsonify({
        'status': 'fail',
        'data': {
            'error': 'invalid input'
        }
    }), 422


@app.errorhandler(405)
def method_not_allowed(_: Exception) -> ResponseReturnValue:
    return jsonify({
        'status': 'fail',
        'data': {
            'error': 'method not allowed'
        }
    }), 405


@app.errorhandler(401)
def unathorized(_: Exception) -> ResponseReturnValue:
    return jsonify({
        'status': 'fail',
        'data': {
            'error': 'you are unauthorized to perform this action'
        }
    }), 401


@app.errorhandler(AbortException)
def abort_error(err: Exception) -> ResponseReturnValue:
    return jsonify({
        'status': 'fail',
        'data': err.error
    }), err.code


#status route
@app.route('/status', methods=['GET'])
def app_status() -> ResponseReturnValue:
    """
    Get the status of the application
    """
    return jsonify({
        'status': 'success',
        'data': {
            'app_status': 'active'
        }
    }), 200


#app views
import os
from models import (
    Company,
    Project,
    InvalidToken
)

from flask_jwt_extended import (
    get_jwt,
    jwt_required,
    create_access_token
)


@app.route('/login', methods=['POST'])
def login() -> ResponseReturnValue:
    from auth import Auth

    form_data = request.form.to_dict()
    if not validate_input(LoginSchema, **form_data):
        abort(422)

    auth = Auth()
    user = auth.authenticate_user(form_data['email'], form_data['password'])
    access_token = create_access_token(identity=user.id)
    return jsonify({
        'status': 'success',
        'access_token': access_token
    }), 200


@app.route('/logout', methods=['GET'])
@jwt_required()
def logout() -> ResponseReturnValue:
    """
    Log out user
    """
    jti = get_jwt()['jti']
    db.save_new(InvalidToken, jti=jti)

    return jsonify({
        'status': 'success',
        'data': {}
    }), 200


@app.route('/change-password', methods=['POST'])
@jwt_required()
def change_password() -> ResponseReturnValue:
    from auth import Auth
    from flask_jwt_extended import get_jwt_identity

    form_data = request.form.to_dict()
    if not validate_input(PasswordSchema, **form_data):
        abort(422)

    auth = Auth()
    user = db.get(User, id=get_jwt_identity())
    user = auth.authenticate_user(user.email, form_data['current_password'])
    user = db.update(User, id=user.id, password=form_data['new_password'])
    return jsonify({
        'status': 'success',
        'data': {
            'message': 'password changed'
        }
    }), 200


@app.route('/companies/<string:id>', methods=['GET'])
def get_a_company(id: str) -> ResponseReturnValue:
    company = db.get(Company, id=id)
    if not company:
        abort(404)

    return jsonify({
        'status': 'success',
        'data': company.to_dict()
    }), 200


@app.route('/projects/<string:id>', methods=['GET'])
def get_a_project(id: str) -> ResponseReturnValue:
    project = db.get(Project, id=id)
    if not project:
        abort(404)

    return jsonify({
        'status': 'success',
        'data': project.to_dict()
    }), 200


@app.route('/companies', methods=['GET'])
def get_companies() -> ResponseReturnValue:
    companies = [company.to_dict() for company in db.get_all(Company)]

    return jsonify({
        'status': 'success',
        'data': companies
    }), 200


@app.route('/projects', methods=['GET'])
def get_projects() -> ResponseReturnValue:
    projects = [project.to_dict() for project in db.get_all(Project)]
    return jsonify({
        'status': 'success',
        'data': projects
    }), 200


@app.route('/companies/<string:id>', methods=['DELETE'])
@jwt_required()
def delete_a_company(id: str) -> ResponseReturnValue:
    db.delete(Company, id=id)
    return jsonify({
        'status': 'success',
        'data': {}
    }), 200


@app.route('/projects/<string:id>', methods=['DELETE'])
@jwt_required()
def delete_a_project(id: str) -> ResponseReturnValue:
    db.delete(Project, id=id)
    return jsonify({
        'status': 'success',
        'data': {}
    }), 200


@app.route('/companies', methods=['POST'])
@jwt_required()
def create_a_company() -> ResponseReturnValue:
    form_data = request.form.to_dict()
    if not validate_input(CompanySchema, **form_data):
        abort(422)

    company = db.save_new(Company, **form_data)
    return jsonify({
        'status': 'success',
        'data': company.to_dict()
    }), 201


@app.route('/projects', methods=['POST'])
@jwt_required()
def create_a_project() -> ResponseReturnValue:
    form_data = request.form.to_dict()
    if not validate_input(ProjectSchema, **form_data):
        abort(422)

    project = db.save_new(Project, **form_data)
    image = request.files.get('image')
    if image:
        os.makedirs(os.path.join(app.root_path, os.getenv('UPLOAD_DIR')), exist_ok=True)
        filename = project.id + os.path.splitext(image.filename)[1]
        file_path = os.path.join(app.root_path, os.getenv('UPLOAD_DIR'), filename)
        image.save(file_path)
        db.update(Project, id=project.id, image=filename)

    return jsonify({
        'status': 'success',
        'data': project.to_dict()
    }), 201


@app.route('/companies/<string:id>', methods=['PATCH'])
@jwt_required()
def update_a_company(id: str) -> ResponseReturnValue:
    form = request.form.to_dict()
    if not validate_input(CompanySchema, **form):
        abort(422)

    form_data = {}
    for key, val in form.items():
        if val is None:
            continue

        form_data[key] = val

    company = db.update(Company, id, **form_data)
    return jsonify({
        'status': 'success',
        'data': company.to_dict()
    }), 200


@app.route('/projects/<string:id>', methods=['PATCH'])
@jwt_required()
def update_a_project(id: str) -> ResponseReturnValue:
    form = request.form.to_dict()
    if not validate_input(ProjectSchema, **form):
        abort(422)

    form_data = {}
    for key, val in form.items():
        if val is None:
            continue

        form_data[key] = val

    print(form_data)
    project = db.update(Project, id, **form_data)
    image = request.files.get('image')
    if image:
        os.makedirs(os.path.join(app.root_path, os.getenv('UPLOAD_DIR')), exist_ok=True)
        filename = project.id + os.path.splitext(image.filename)[1]
        file_path = os.path.join(app.root_path, os.getenv('UPLOAD_DIR'), filename)
        image.save(file_path)
        db.update(Project, id=project.id, image=filename)

    return jsonify({
        'status': 'success',
        'data': project.to_dict()
    }), 200


@app.route('/serve-image/<string:filename>', methods=['GET'])
def serve_image(filename: str) -> ResponseReturnValue:
    from flask import send_from_directory

    return send_from_directory(getenv('UPLOAD_DIR'), filename, as_attachment=False)


if __name__ == '__main__':
    port = int(getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
