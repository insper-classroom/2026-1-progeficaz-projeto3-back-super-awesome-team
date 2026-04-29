from flask import Blueprint, request, jsonify
from ..services.pendency_services import (
    confirm_debtor_payment_service,
    confirm_creditor_payment_service,
    get_user_pendencies_service,
    get_bill_pendencies_service,
    get_pendency_service
)
from ..utils import jwt_required

pendency_bp = Blueprint('pendency', __name__)

@pendency_bp.route('/pendencies', methods=['GET'])
@jwt_required
def get_user_pendencies():
    user_email = request.current_user
    result, error = get_user_pendencies_service(user_email)
    if error:
        return jsonify(error), 400
    return jsonify(result), 200


@pendency_bp.route('/pendencies/<pendency_id>', methods=['GET'])
@jwt_required
def get_pendency(pendency_id):
    result, error = get_pendency_service(pendency_id)
    if error:
        return jsonify(error), 404
    return jsonify(result), 200


@pendency_bp.route('/bills/<bill_id>/pendencies', methods=['GET'])
@jwt_required
def get_bill_pendencies(bill_id):
    result, error = get_bill_pendencies_service(bill_id)
    if error:
        return jsonify(error), 400
    return jsonify({'pendencies': result}), 200


@pendency_bp.route('/pendencies/<pendency_id>/confirm-debtor', methods=['PUT'])
@jwt_required
def confirm_debtor_payment(pendency_id):
    user_email = request.current_user
    result, error = confirm_debtor_payment_service(pendency_id, user_email)
    if error:
        status_code = 404 if 'não encontrada' in error.get('error', '') else 400
        return jsonify(error), status_code
    return jsonify(result), 200


@pendency_bp.route('/pendencies/<pendency_id>/confirm-creditor', methods=['PUT'])
@jwt_required
def confirm_creditor_payment(pendency_id):
    user_email = request.current_user
    result, error = confirm_creditor_payment_service(pendency_id, user_email)
    if error:
        status_code = 404 if 'não encontrada' in error.get('error', '') else 400
        return jsonify(error), status_code
    return jsonify(result), 200
