import bcrypt
import gevent
from ..extensions import mongo
from ..models import User
from ..schemas import LoginSchema
from ..utils import (
    generate_token,
    get_user_by_email,
    send_welcome_email,
    send_reset_code_email,
)
import os
import uuid
from google_auth_oauthlib.flow import Flow
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
import secrets
from datetime import datetime, timezone, timedelta


schema = LoginSchema()


def _normalize_utc_datetime(value):
    if value and value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def login_service(data):
    errors = schema.validate(data)
    if errors:
        return None, errors

    user = get_user_by_email(data["email"])
    if not user:
        return None, {"error": "Credenciais inválidas"}

    if not user.get("password"):
        return None, {"error": "Credenciais inválidas"}

    if not bcrypt.checkpw(
        data["password"].encode("utf-8"), user["password"].encode("utf-8")
    ):
        return None, {"error": "Credenciais inválidas"}

    if not user.get("is_verified", False):
        return None, {"error": "E-mail ainda não verificado"}

    token = generate_token(data["email"])
    return {"token": token}, None


GOOGLE_SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
]

GOOGLE_CLIENT_CONFIG = {
    "web": {
        "client_id": os.getenv("GOOGLE_WEB_CLIENT_ID"),
        "client_secret": os.getenv("GOOGLE_WEB_CLIENT_SECRET"),
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
    }
}

GOOGLE_REDIRECT_URI = os.getenv(
    "GOOGLE_REDIRECT_URI", "http://localhost:5000/auth/google/callback"
)


def get_google_auth_url():
    flow = Flow.from_client_config(
        GOOGLE_CLIENT_CONFIG,
        scopes=GOOGLE_SCOPES,
        redirect_uri=GOOGLE_REDIRECT_URI,
    )
    auth_url, state = flow.authorization_url(prompt="consent")
    return auth_url, state, flow.code_verifier


def google_callback_service(code, code_verifier=None):
    try:
        flow = Flow.from_client_config(
            GOOGLE_CLIENT_CONFIG,
            scopes=GOOGLE_SCOPES,
            redirect_uri=GOOGLE_REDIRECT_URI,
        )
        flow.fetch_token(code=code, code_verifier=code_verifier)
        credentials = flow.credentials

        id_info = id_token.verify_oauth2_token(
            credentials.id_token,
            google_requests.Request(),
            os.getenv("GOOGLE_WEB_CLIENT_ID"),
        )

        email = id_info["email"]
        name = id_info.get("name", email)

        user = get_user_by_email(email)
        if not user:
            new_user = User(name, email, auth_provider="google")
            new_user.is_verified = True
            mongo["users"].insert_one(new_user.to_dictionary())
            gevent.spawn(send_welcome_email, name, email)

        token = generate_token(email)
        return {"token": token}, None
    except Exception as e:
        return None, {"error": str(e)}


def request_password_reset_service(data):
    email = data.get("email", "").strip()
    if not email:
        return {"message": "Se o e-mail existir, o código será enviado"}, None

    user = get_user_by_email(email)
    if user:  # não revela se o e-mail existe ou não na resposta
        code = f"{secrets.randbelow(1000000):06d}"
        expires = datetime.now(timezone.utc) + timedelta(minutes=10)
        mongo["users"].update_one(
            {"email": email},
            {"$set": {"reset_code": code, "reset_code_expires": expires}},
        )
        gevent.spawn(send_reset_code_email, user["name"], email, code)

    return {"message": "Se o e-mail existir, o código será enviado"}, None


def verify_reset_code_service(data):
    email = data.get("email", "").strip()
    code = str(data.get("code", "")).strip()
    if not email or not code:
        return None, {"error": "E-mail e código são obrigatórios"}

    user = get_user_by_email(email)
    if not user:
        return None, {"error": "Código inválido ou expirado"}

    stored_code = user.get("reset_code")
    expires = _normalize_utc_datetime(user.get("reset_code_expires"))
    if not stored_code or stored_code != code:
        return None, {"error": "Código inválido ou expirado"}
    if not expires or datetime.now(timezone.utc) > expires:
        return None, {"error": "Código expirado"}

    reset_token = str(uuid.uuid4())
    token_expires = datetime.now(timezone.utc) + timedelta(minutes=15)
    mongo["users"].update_one(
        {"email": email},
        {
            "$set": {"reset_token": reset_token, "reset_token_expires": token_expires},
            "$unset": {"reset_code": "", "reset_code_expires": ""},
        },
    )
    return {"reset_token": reset_token}, None


def reset_password_service(data):
    reset_token = data.get("reset_token", "").strip()
    new_password = data.get("new_password", "").strip()
    if not reset_token or not new_password:
        return None, {"error": "reset_token e new_password são obrigatórios"}

    user = mongo["users"].find_one({"reset_token": reset_token})
    if not user:
        return None, {"error": "Token inválido ou expirado"}

    expires = _normalize_utc_datetime(user.get("reset_token_expires"))
    if not expires or datetime.now(timezone.utc) > expires:
        return None, {"error": "Token expirado"}

    hashed = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt()).decode(
        "utf-8"
    )
    mongo["users"].update_one(
        {"reset_token": reset_token},
        {
            "$set": {"password": hashed},
            "$unset": {"reset_token": "", "reset_token_expires": ""},
        },
    )
    return {"message": "Senha alterada com sucesso"}, None
