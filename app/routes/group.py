from flask import Blueprint, request, jsonify
from ..extensions import mongo
from ..models.group import Group
from ..services.group_services import create_group_service
from ..utils.jwt_utils import jwt_required

group_bp = Blueprint('group', __name__)

@group_bp.route('/group', methods=['POST'])
@jwt_required
def create_group():
    data = request.get_json()
    result, error = create_group_service(data)
    if error:
        return jsonify(error), 400
    return jsonify(result), 201