from flask import Blueprint, request, jsonify
from ..extensions import mongo
from ..models.user import User
from ..services.user_services import create_user_service

user_bp = Blueprint('user', __name__)

@user_bp.route('/user', methods=['POST'])
def create_user():
    data = request.get_json()
    result, error = create_user_service(data)
    if error:
        return jsonify(error), 400
    return jsonify(result), 201

@user_bp.route('/user', methods=['GET'])
def get_users():
    users = list(mongo['users'].find())
    for user in users:
        user['_id'] = str(user['_id'])
    return jsonify(users), 200