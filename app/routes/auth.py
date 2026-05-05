import os
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

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


def _frontend_target(env_name, default_path):
    configured_url = os.getenv(env_name)
    if configured_url:
        return configured_url

    frontend_url = os.getenv("FRONTEND_URL")
    if not frontend_url:
        return None

    return f"{frontend_url.rstrip('/')}/{default_path.lstrip('/')}"


def _with_url_params(url, query_params=None, fragment_params=None):
    parts = urlsplit(url)
    query = dict(parse_qsl(parts.query))
    fragment = dict(parse_qsl(parts.fragment))

    query.update(query_params or {})
    fragment.update(fragment_params or {})

    return urlunsplit(
        (
            parts.scheme,
            parts.netloc,
            parts.path,
            urlencode(query),
            urlencode(fragment),
        )
    )


def _redirect_to_frontend(url, query_params=None, fragment_params=None):
    return redirect(_with_url_params(url, query_params, fragment_params))


@auth_bp.route("/auth/sessions", methods=["POST"])
def login():
    data = request.get_json()
    result, error = login_service(data)
    if error:
        if error.get("error") == "E-mail ainda não verificado":
            return jsonify(error), 403
        return jsonify(error), 401
    return jsonify(result), 200


@auth_bp.route("/auth/email-verifications/<token>", methods=["GET"])
def verify_email(token):
    result, error = verify_email_service(token)
    frontend_url = _frontend_target("FRONTEND_EMAIL_VERIFIED_URL", "/email-verified")
    if error:
        if frontend_url:
            return _redirect_to_frontend(
                frontend_url,
                {"status": "error", "message": error.get("error", "")},
            )
        if error.get("error") == "Token inválido ou expirado":
            return jsonify(error), 404
        return jsonify(error), 400
    if frontend_url:
        return _redirect_to_frontend(
            frontend_url,
            {"status": "success", "message": result.get("message", "")},
        )
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
    frontend_url = _frontend_target("FRONTEND_AUTH_CALLBACK_URL", "/auth/callback")
    if error:
        if frontend_url:
            return _redirect_to_frontend(
                frontend_url,
                {"status": "error", "message": error.get("error", "")},
            )
        return jsonify(error), 400
    if frontend_url:
        return _redirect_to_frontend(
            frontend_url,
            {"status": "success"},
            {"token": result["token"]},
        )
    return jsonify(result), 200


@auth_bp.route("/auth/password-resets", methods=["POST"])
def forgot_password():
    data = request.get_json()
    result, error = request_password_reset_service(data)
    if error:
        return jsonify(error), 400
    return jsonify(result), 200


@auth_bp.route("/auth/password-resets/verify", methods=["POST"])
def verify_reset_code():
    data = request.get_json()
    result, error = verify_reset_code_service(data)
    if error:
        return jsonify(error), 400
    return jsonify(result), 200


@auth_bp.route("/auth/password", methods=["PATCH"])
def reset_password():
    data = request.get_json()
    result, error = reset_password_service(data)
    if error:
        return jsonify(error), 400
    return jsonify(result), 200
