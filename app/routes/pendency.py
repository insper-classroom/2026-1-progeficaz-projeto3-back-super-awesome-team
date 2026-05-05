from flask import Blueprint, request, jsonify
from ..services import (
    confirm_debtor_payment_service,
    confirm_creditor_payment_service,
    get_user_pendencies_service,
    get_bill_pendencies_service,
    get_pendency_service,
    get_group_pendencies_service,
)
from ..utils import jwt_required, http_status_for_service_error

pendency_bp = Blueprint("pendency", __name__)


@pendency_bp.route("/pendencies", methods=["GET"])
@jwt_required
def get_user_pendencies():
    user_email = request.current_user
    result, error = get_user_pendencies_service(user_email)
    if error:
        return jsonify(error), http_status_for_service_error(error)
    return jsonify(result), 200


@pendency_bp.route("/pendencies/<pendency_id>", methods=["GET"])
@jwt_required
def get_pendency(pendency_id):
    user_email = request.current_user
    result, error = get_pendency_service(pendency_id, user_email)
    if error:
        return jsonify(error), http_status_for_service_error(error)
    return jsonify(result), 200


@pendency_bp.route("/bill/<bill_id>/pendencies", methods=["GET"])
@jwt_required
def get_bill_pendencies(bill_id):
    user_email = request.current_user
    result, error = get_bill_pendencies_service(bill_id, user_email)
    if error:
        return jsonify(error), http_status_for_service_error(error)
    return jsonify({"pendencies": result}), 200


@pendency_bp.route("/group/<group_id>/pendencies", methods=["GET"])
@jwt_required
def get_group_pendencies(group_id):
    user_email = request.current_user
    result, error = get_group_pendencies_service(group_id, user_email)
    if error:
        return jsonify(error), http_status_for_service_error(error)
    return jsonify({"pendencies": result}), 200


@pendency_bp.route("/pendencies/<pendency_id>/debtor-confirmation", methods=["PUT"])
@jwt_required
def confirm_debtor_payment(pendency_id):
    user_email = request.current_user
    result, error = confirm_debtor_payment_service(pendency_id, user_email)
    if error:
        return jsonify(error), http_status_for_service_error(error)
    return jsonify(result), 200


@pendency_bp.route("/pendencies/<pendency_id>/creditor-confirmation", methods=["PUT"])
@jwt_required
def confirm_creditor_payment(pendency_id):
    user_email = request.current_user
    result, error = confirm_creditor_payment_service(pendency_id, user_email)
    if error:
        return jsonify(error), http_status_for_service_error(error)
    return jsonify(result), 200
