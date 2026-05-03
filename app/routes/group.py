from flask import Blueprint, request, jsonify
from ..services import (
    create_group_service,
    get_user_groups_service,
    get_group_service,
    update_group_service,
    delete_group_service,
)
from ..utils import jwt_required, http_status_for_service_error

group_bp = Blueprint("group", __name__)


@group_bp.route("/group", methods=["POST"])
@jwt_required
def create_group():
    data = request.get_json()
    user_email = request.current_user
    result, error = create_group_service(data, user_email)
    if error:
        return jsonify(error), http_status_for_service_error(error)
    return jsonify(result), 201


@group_bp.route("/group", methods=["GET"])
@jwt_required
def get_user_groups():
    user_email = request.current_user
    groups, error = get_user_groups_service(user_email)
    if error:
        return jsonify(error), 500
    return jsonify({"groups": groups}), 200


@group_bp.route("/group/<group_id>", methods=["GET"])
@jwt_required
def get_group(group_id):
    user_email = request.current_user
    group, error = get_group_service(group_id, user_email)
    if error:
        return jsonify(error), http_status_for_service_error(error)
    return jsonify(group), 200


@group_bp.route("/group/<group_id>", methods=["PUT"])
@jwt_required
def update_group(group_id):
    data = request.get_json()
    user_email = request.current_user
    result, error = update_group_service(group_id, data, user_email)
    if error:
        return jsonify(error), http_status_for_service_error(error)
    return jsonify(result), 200


@group_bp.route("/group/<group_id>", methods=["DELETE"])
@jwt_required
def delete_group(group_id):
    user_email = request.current_user
    result, error = delete_group_service(group_id, user_email)
    if error:
        return jsonify(error), http_status_for_service_error(error)
    return jsonify(result), 200
