from flask import Blueprint, request, jsonify
from ..extensions import mongo
from ..models import User
from ..services import create_user_service, update_user_service
from ..utils import jwt_required

user_bp = Blueprint('user', __name__)

@user_bp.route('/user', methods=['POST'])
def create_user():
    data = request.get_json()
    result, error = create_user_service(data)
    if error:
        return jsonify(error), 400
    return jsonify(result), 201

@user_bp.route('/user', methods=['GET'])
@jwt_required
def get_users():
    users = list(mongo['users'].find())
    for user in users:
        user['_id'] = str(user['_id'])
        user.pop('password', None)
        user.pop('senha', None)
    return jsonify(users), 200



@user_bp.route('/user', methods=['PUT'])
@jwt_required
def update_users():
    data = request.get_json()
    user_id = data.get("user_id")

    if not user_id:
        return jsonify({"error": "user_id é obrigatório"}), 400
    
    resultado, error = update_user_service(user_id, data)

    if error:
        return jsonify(error), 400
    
    return jsonify(resultado), 200