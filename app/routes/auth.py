from flask import Blueprint, request, jsonify
from ..services import login_service, verify_email_service

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/auth/login", methods=["POST"])
def login():
    data = request.get_json()
    result, error = login_service(data)
    if error:
        if error.get("error") == "E-mail ainda não verificado":
            return jsonify(error), 403
        return jsonify(error), 401
    return jsonify(result), 200


@auth_bp.route("/auth/verify-email/<token>", methods=["GET"])
def verify_email(token):
    result, error = verify_email_service(token)
    if error:
        return jsonify(error), 400
    return jsonify(result), 200
