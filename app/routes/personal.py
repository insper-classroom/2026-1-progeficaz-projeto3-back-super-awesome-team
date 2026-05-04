from flask import Blueprint, jsonify, request

from ..services import get_personal_summary_service
from ..utils import http_status_for_service_error, jwt_required

personal_bp = Blueprint("personal", __name__)


@personal_bp.route("/personal/summary", methods=["GET"])
@jwt_required
def get_personal_summary():
    result, error = get_personal_summary_service(request.current_user)
    if error:
        return jsonify(error), http_status_for_service_error(error)
    return jsonify(result), 200
