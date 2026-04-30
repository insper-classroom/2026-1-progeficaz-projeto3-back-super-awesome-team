import bcrypt
from ..extensions import mongo
from ..schemas import LoginSchema
from ..utils import generate_token, get_user_by_email

schema = LoginSchema()


def login_service(data):
    errors = schema.validate(data)
    if errors:
        return None, errors

    user = get_user_by_email(data["email"])
    if not user:
        return None, {"error": "Credenciais inválidas"}

    if not bcrypt.checkpw(
        data["password"].encode("utf-8"), user["password"].encode("utf-8")
    ):
        return None, {"error": "Credenciais inválidas"}

    if not user.get("is_verified", False):
        return None, {"error": "E-mail ainda não verificado"}

    token = generate_token(data["email"])
    return {"token": token}, None
