from flask import Blueprint, jsonify, request

from ..services import (
    add_goal_contribution_service,
    create_goal_service,
    delete_goal_service,
    get_goal_service,
    get_group_goals_service,
    get_user_goals_service,
    update_goal_service,
)
from ..utils import http_status_for_service_error, jwt_required

goal_bp = Blueprint("goal", __name__)


@goal_bp.route("/goal", methods=["POST"])
@jwt_required
def create_goal():
    data = request.get_json() or {}
    result, error = create_goal_service(data, request.current_user)
    if error:
        return jsonify(error), http_status_for_service_error(error)
    return jsonify(result), 201


@goal_bp.route("/goal", methods=["GET"])
@jwt_required
def get_user_goals():
    result, error = get_user_goals_service(request.current_user)
    if error:
        return jsonify(error), http_status_for_service_error(error)
    return jsonify({"goals": result}), 200


@goal_bp.route("/group/<group_id>/goal", methods=["GET"])
@jwt_required
def get_group_goals(group_id):
    result, error = get_group_goals_service(group_id, request.current_user)
    if error:
        return jsonify(error), http_status_for_service_error(error)
    return jsonify({"goals": result}), 200


@goal_bp.route("/goal/<goal_id>", methods=["GET"])
@jwt_required
def get_goal(goal_id):
    result, error = get_goal_service(goal_id, request.current_user)
    if error:
        return jsonify(error), http_status_for_service_error(error)
    return jsonify(result), 200


@goal_bp.route("/goal/<goal_id>", methods=["PUT"])
@jwt_required
def update_goal(goal_id):
    data = request.get_json() or {}
    result, error = update_goal_service(goal_id, data, request.current_user)
    if error:
        return jsonify(error), http_status_for_service_error(error)
    return jsonify(result), 200


@goal_bp.route("/goal/<goal_id>", methods=["DELETE"])
@jwt_required
def delete_goal(goal_id):
    result, error = delete_goal_service(goal_id, request.current_user)
    if error:
        return jsonify(error), http_status_for_service_error(error)
    return jsonify(result), 200


@goal_bp.route("/goal/<goal_id>/contribution", methods=["POST"])
@jwt_required
def add_goal_contribution(goal_id):
    data = request.get_json() or {}
    result, error = add_goal_contribution_service(goal_id, data, request.current_user)
    if error:
        return jsonify(error), http_status_for_service_error(error)
    return jsonify(result), 201
