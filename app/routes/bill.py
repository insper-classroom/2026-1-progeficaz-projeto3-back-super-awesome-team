from flask import Blueprint, request, jsonify
from ..extensions import mongo
from ..models.bill import Bill
from ..services.bill_services import create_bill_service
from ..utils.jwt_utils import jwt_required

bill_bp = Blueprint('bill', __name__)

@bill_bp.route('/bill', methods=['POST'])
@jwt_required
def create_bill():
    data = request.get_json()
    result, error = create_bill_service(data)
    if error:
        return jsonify(error), 400
    return jsonify(result), 201
