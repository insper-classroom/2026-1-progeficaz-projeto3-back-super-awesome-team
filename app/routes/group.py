from flask import Blueprint, request, jsonify
from ..extensions import mongo
from ..models import Group
from ..services import create_group_service
from ..utils import jwt_required

group_bp = Blueprint("group", __name__)


@group_bp.route("/group", methods=["POST"])
@jwt_required
def create_group():
    data = request.get_json()
    user_email = request.current_user
    result, error = create_group_service(data, user_email)
    if error:
        return jsonify(error), 400
    return jsonify(result), 201
