from flask import Blueprint, request, jsonify
from ..services import login_service

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/auth/login", methods=["POST"])
def login():
    data = request.get_json()
    result, error = login_service(data)
    if error:
        return jsonify(error), 401
    return jsonify(result), 200
