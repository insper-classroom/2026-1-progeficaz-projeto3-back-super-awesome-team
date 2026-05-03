from flask import Blueprint, request, jsonify
from ..extensions import mongo
from ..models import Bill
from ..services import (
    create_bill_service,
    get_user_bills_service,
    get_group_bills_service,
    get_bill_service,
    update_bill_service,
    delete_bill_service,
    mark_bill_as_paid_service,
)
from ..utils import jwt_required

bill_bp = Blueprint("bill", __name__)


@bill_bp.route("/bill", methods=["POST"])
@jwt_required
def create_bill():
    data = request.get_json()
    user_email = request.current_user
    result, error = create_bill_service(data, user_email)
    if error:
        return jsonify(error), 400
    return jsonify(result), 201


@bill_bp.route("/bill", methods=["GET"])
@jwt_required
def get_user_bills():
    user_email = request.current_user
    bills, error = get_user_bills_service(user_email)
    if error:
        return jsonify(error), 500
    return jsonify({"bills": bills}), 200


@bill_bp.route("/group/<group_id>/bill", methods=["GET"])
@jwt_required
def get_group_bills(group_id):
    user_email = request.current_user
    bills, error = get_group_bills_service(group_id, user_email)
    if error:
        status_code = 404 if "não encontrado" in error.get("error", "") else 403
        return jsonify(error), status_code
    return jsonify({"bills": bills}), 200


@bill_bp.route("/bill/<bill_id>", methods=["GET"])
@jwt_required
def get_bill(bill_id):
    user_email = request.current_user
    bill, error = get_bill_service(bill_id, user_email)
    if error:
        status_code = 404 if "não encontrado" in error.get("error", "") else 403
        return jsonify(error), status_code
    return jsonify(bill), 200


@bill_bp.route("/bill/<bill_id>", methods=["PUT"])
@jwt_required
def update_bill(bill_id):
    data = request.get_json()
    user_email = request.current_user
    result, error = update_bill_service(bill_id, data, user_email)
    if error:
        status_code = 404 if "não encontrado" in error.get("error", "") else 400
        return jsonify(error), status_code
    return jsonify(result), 200


@bill_bp.route("/bill/<bill_id>", methods=["DELETE"])
@jwt_required
def delete_bill(bill_id):
    user_email = request.current_user
    result, error = delete_bill_service(bill_id, user_email)
    if error:
        status_code = 404 if "não encontrado" in error.get("error", "") else 403
        return jsonify(error), status_code
    return jsonify(result), 200


@bill_bp.route("/bill/<bill_id>/mark-as-paid", methods=["PUT"])
@jwt_required
def mark_bill_as_paid(bill_id):
    user_email = request.current_user
    result, error = mark_bill_as_paid_service(bill_id, user_email)
    if error:
        error_message = error.get("error", "")
        if "não encontrada" in error_message:
            return jsonify(error), 404
        else:
            return jsonify(error), 403
    return jsonify(result), 200
