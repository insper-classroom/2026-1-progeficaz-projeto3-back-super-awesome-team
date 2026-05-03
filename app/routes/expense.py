from flask import Blueprint, request, jsonify
from ..services import (
    create_expense_service,
    get_expense_service,
    get_user_expenses_service,
    update_expense_service,
    delete_expense_service,
)
from ..utils import jwt_required, http_status_for_service_error

expense_bp = Blueprint("expense", __name__)


@expense_bp.route("/expense", methods=["POST"])
@jwt_required
def create_expense():
    data = request.get_json()
    user_email = request.current_user
    result, error = create_expense_service(data, user_email)
    if error:
        return jsonify(error), http_status_for_service_error(error)
    return jsonify(result), 201


@expense_bp.route("/expense/<expense_id>", methods=["GET"])
@jwt_required
def get_expense(expense_id):
    user_email = request.current_user
    expense, error = get_expense_service(expense_id, user_email)
    if error:
        return jsonify(error), http_status_for_service_error(error)
    return jsonify(expense), 200


@expense_bp.route("/expense", methods=["GET"])
@jwt_required
def get_user_expenses():
    user_email = request.current_user
    expenses, error = get_user_expenses_service(user_email)
    if error:
        return jsonify(error), 500
    return jsonify({"expenses": expenses}), 200


@expense_bp.route("/expense/<expense_id>", methods=["PUT"])
@jwt_required
def update_expense(expense_id):
    data = request.get_json()
    user_email = request.current_user
    result, error = update_expense_service(expense_id, data, user_email)
    if error:
        return jsonify(error), http_status_for_service_error(error)
    return jsonify(result), 200


@expense_bp.route("/expense/<expense_id>", methods=["DELETE"])
@jwt_required
def delete_expense(expense_id):
    user_email = request.current_user
    result, error = delete_expense_service(expense_id, user_email)
    if error:
        return jsonify(error), http_status_for_service_error(error)
    return jsonify(result), 200
