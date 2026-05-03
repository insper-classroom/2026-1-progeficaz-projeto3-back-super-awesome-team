import os
from flask import Blueprint, request, jsonify, redirect, session
from ..services import (
    login_service,
    verify_email_service,
    get_google_auth_url,
    google_callback_service,
    request_password_reset_service,
    verify_reset_code_service,
    reset_password_service,
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
        if error.get("error") == "Token inválido ou expirado":
            return jsonify(error), 404
        return jsonify(error), 400
    return jsonify(result), 200


@auth_bp.route("/auth/google", methods=["GET"])
def google_login():
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    auth_url, state, code_verifier = get_google_auth_url()
    session["code_verifier"] = code_verifier
    return redirect(auth_url)


@auth_bp.route("/auth/google/callback", methods=["GET"])
def google_callback():
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    code = request.args.get("code")
    code_verifier = session.pop("code_verifier", None)
    result, error = google_callback_service(code, code_verifier)
    if error:
        return jsonify(error), 400
    return jsonify(result), 200


@auth_bp.route("/auth/forgot-password", methods=["POST"])
def forgot_password():
    data = request.get_json()
    result, error = request_password_reset_service(data)
    if error:
        return jsonify(error), 400
    return jsonify(result), 200


@auth_bp.route("/auth/verify-reset-code", methods=["POST"])
def verify_reset_code():
    data = request.get_json()
    result, error = verify_reset_code_service(data)
    if error:
        return jsonify(error), 400
    return jsonify(result), 200


@auth_bp.route("/auth/reset-password", methods=["POST"])
def reset_password():
    data = request.get_json()
    result, error = reset_password_service(data)
    if error:
        return jsonify(error), 400
    return jsonify(result), 200
