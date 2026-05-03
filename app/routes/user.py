from flask import Blueprint, request, jsonify
from ..services import (
    create_user_service,
    update_user_service,
    delete_user_service,
    get_current_user_service,
)
from ..utils import jwt_required, http_status_for_service_error

user_bp = Blueprint("user", __name__)


@user_bp.route("/user", methods=["POST"])
def create_user():
    data = request.get_json()
    result, error = create_user_service(data)
    if error:
        return jsonify(error), http_status_for_service_error(error)
    return jsonify(result), 201


@user_bp.route("/user/me", methods=["GET"])
@jwt_required
def get_current_user():
    user, error = get_current_user_service(request.current_user)
    if error:
        return jsonify(error), http_status_for_service_error(error)
    return jsonify(user), 200


@user_bp.route("/user", methods=["PUT"])
@jwt_required
def update_users():
    data = request.get_json() or {}

    resultado, error = update_user_service(request.current_user, data)

    if error:
        return jsonify(error), http_status_for_service_error(error)

    return jsonify(resultado), 200


@user_bp.route("/user", methods=["DELETE"])
@jwt_required
def delete_user():
    data = request.get_json() or {}

    result, error = delete_user_service(request.current_user, data)

    if error:
        return jsonify(error), http_status_for_service_error(error)

    return jsonify(result), 200