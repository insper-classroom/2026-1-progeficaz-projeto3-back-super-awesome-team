import os
from flask import Blueprint, request, jsonify, redirect
from ..services import (
    login_service,
    verify_email_service,
    get_google_auth_url,
    google_callback_service,
)

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


@auth_bp.route("/auth/google", methods=["GET"])
def google_login():
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    auth_url, state = get_google_auth_url()
    return redirect(auth_url)


@auth_bp.route("/auth/google/callback", methods=["GET"])
def google_callback():
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    code = request.args.get("code")
    result, error = google_callback_service(code)
    if error:
        return jsonify(error), 400
    return jsonify(result), 200
