import bcrypt
from ..extensions import mongo
from ..models import User
from ..schemas import LoginSchema
from ..utils import generate_token, get_user_by_email
import os
from google_auth_oauthlib.flow import Flow
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

schema = LoginSchema()


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
        "client_id": os.getenv("CLIENT_ID"),
        "client_secret": os.getenv("CLIENT_SECRET"),
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
    }
}

GOOGLE_REDIRECT_URI = "http://localhost:5000/auth/google/callback"


def get_google_auth_url():
    flow = Flow.from_client_config(
        GOOGLE_CLIENT_CONFIG,
        scopes=GOOGLE_SCOPES,
        redirect_uri=GOOGLE_REDIRECT_URI,
    )
    auth_url, state = flow.authorization_url(prompt="consent")
    return auth_url, state


def google_callback_service(code):
    try:
        flow = Flow.from_client_config(
            GOOGLE_CLIENT_CONFIG,
            scopes=GOOGLE_SCOPES,
            redirect_uri=GOOGLE_REDIRECT_URI,
        )
        flow.fetch_token(code=code)
        credentials = flow.credentials

        id_info = id_token.verify_oauth2_token(
            credentials.id_token,
            google_requests.Request(),
            os.getenv("CLIENT_ID"),
        )

        email = id_info["email"]
        name = id_info.get("name", email)

        user = get_user_by_email(email)
        if not user:
            new_user = User(name, email, auth_provider="google")
            new_user.is_verified = True
            mongo["users"].insert_one(new_user.to_dictionary())

        token = generate_token(email)
        return {"token": token}, None
    except Exception as e:
        return None, {"error": str(e)}
