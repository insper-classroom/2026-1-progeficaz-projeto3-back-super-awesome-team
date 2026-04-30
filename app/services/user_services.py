from ..models import User
from ..extensions import mongo
from ..schemas import UserSchema, UpdateUserSchema
from ..utils import send_email, get_user_by_email
from bson import ObjectId
import bcrypt
import gevent

schema = UserSchema()
update_schema = UpdateUserSchema()


def _email_error_handler(greenlet):
    print(f"Erro ao enviar e-mail: {greenlet.exception}")


def create_user_service(data):
    erros = schema.validate(data)
    if erros:
        return None, erros

    existing = get_user_by_email(data["email"])
    if existing:
        return None, {"error": "email já cadastrado"}

    hashed = bcrypt.hashpw(data["password"].encode("utf-8"), bcrypt.gensalt()).decode(
        "utf-8"
    )
    user = User(data["name"], data["email"], hashed)
    mongo["users"].insert_one(user.to_dictionary())

    token = user.verification_token
    subject = "Confirme seu e-mail"
    body = (
        f"Olá {data['name']},\n\n"
        f"Clique no link abaixo para confirmar sua conta:\n\n"
        f"http://localhost:5000/auth/verify-email/{token}\n\n"
        f"Se não foi você, ignore este e-mail."
    )
    gevent.spawn(send_email, subject, body, data["email"]).link_exception(
        _email_error_handler
    )

    return {"message": "OK ✅"}, None


def update_user_service(user_id, data):
    erros = update_schema.validate(data)
    if erros:
        return None, erros
    try:
        oid = ObjectId(user_id)
    except Exception:
        return None, {"error": "ID inválido"}

    user = mongo["users"].find_one({"_id": oid})

    if not user:
        return None, {"error": "Usuário não encontrado"}

    updated_fields = {}

    if "name" in data:
        updated_fields["name"] = data["name"]

    if "password" in data:
        current_password = data.get("current_password")

        if not current_password:
            return None, {"error": "Current password is required to set a new password"}

        if not bcrypt.checkpw(
            current_password.encode("utf-8"), user["password"].encode("utf-8")
        ):
            return None, {"error": "Current password is incorrect"}

        hashed = bcrypt.hashpw(
            data["password"].encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")
        updated_fields["password"] = hashed

    if not updated_fields:
        return None, {"error": "Nenhum campo alterado"}

    mongo["users"].update_one({"_id": oid}, {"$set": updated_fields})

    return {"message": "Usuário atualizado com sucesso"}, None


def verify_email_service(token):
    user = mongo["users"].find_one({"verification_token": token})
    if not user:
        return None, {"error": "Token inválido ou expirado"}
    if user.get("is_verified"):
        return {"message": "Conta já verificada"}, None
    mongo["users"].update_one(
        {"verification_token": token},
        {"$set": {"is_verified": True}, "$unset": {"verification_token": ""}},
    )
    return {"message": "E-mail confirmado com sucesso"}, None
