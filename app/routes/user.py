from flask import Blueprint, request, jsonify
from ..extensions import mongo
from ..models.user import User
from ..schemas.user_schema import UserSchema

schema = UserSchema()
user_bp = Blueprint('user', __name__)

@user_bp.route('/user', methods=['POST'])
def create_user():
    erros = schema.validate(request.get_json())
    if erros:
        return jsonify(erros), 400

    data = request.get_json()
    user = User(data["name"], data["email"], data["password"])
    mongo['users'].insert_one(user.to_dictionary())
    return jsonify({'message': 'OK ✅'}), 201

@user_bp.route('/user', methods=['GET'])
def get_users():
    users = list(mongo['users'].find())
    for user in users:
        user['_id'] = str(user['_id'])  # converte ObjectId para string
    return jsonify(users), 200