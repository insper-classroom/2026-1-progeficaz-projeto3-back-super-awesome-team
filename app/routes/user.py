from flask import Blueprint, request, jsonify
from app.extensions import mongo

user_bp = Blueprint('user', __name__)

@user_bp.route('/user', methods=['POST'])
def create_user():
    data = request.get_json()
    result = mongo['users'].insert_one(data)
    return jsonify({'message': 'OK ✅'}), 201

@user_bp.route('/user', methods=['GET'])
def get_users():
    users = list(mongo['users'].find())
    for user in users:
        user['_id'] = str(user['_id'])  # converte ObjectId para string
    return jsonify(users), 200
