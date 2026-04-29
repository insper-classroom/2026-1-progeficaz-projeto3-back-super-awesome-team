from flask import Blueprint, request, jsonify
from ..extensions import mongo
from ..models import Bill
from ..services import create_bill_service, mark_bill_as_paid_service
from ..utils import jwt_required

bill_bp = Blueprint('bill', __name__)

@bill_bp.route('/bill', methods=['POST'])
@jwt_required
def create_bill():
    data = request.get_json()
    user_email = request.current_user
    result, error = create_bill_service(data, user_email)
    if error:
        return jsonify(error), 400
    return jsonify(result), 201


@bill_bp.route('/bill/<bill_id>/mark-as-paid', methods=['PUT'])
@jwt_required
def mark_bill_as_paid(bill_id):
    user_email = request.current_user
    result, error = mark_bill_as_paid_service(bill_id, user_email)
    if error:
        error_message = error.get('error', '')
        if 'não encontrada' in error_message:
            return jsonify(error), 404
        else:
            return jsonify(error), 403
    return jsonify(result), 200
