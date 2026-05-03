import os
from ..models import User
from ..extensions import mongo
from ..schemas import UserSchema, UpdateUserSchema, DeleteUserSchema
from ..utils import send_email, send_welcome_email, send_confirm_email, get_user_by_email
from bson import ObjectId
import bcrypt
import gevent

schema = UserSchema()
update_schema = UpdateUserSchema()
delete_schema = DeleteUserSchema()


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
    base_url = os.getenv("BASE_URL", "http://localhost:5000")
    confirm_url = f"{base_url}/auth/verify-email/{token}"
    gevent.spawn(
        send_confirm_email, data["name"], data["email"], confirm_url
    ).link_exception(_email_error_handler)

    return {"message": "OK ✅"}, None


def update_user_service(email, data):
    erros = update_schema.validate(data)
    if erros:
        return None, erros

    user = mongo["users"].find_one({"email": email})
    if not user:
        return None, {"error": "Usuário não encontrado"}

    updated_fields = {}

    if "name" in data:
        updated_fields["name"] = data["name"]

    if "password" in data:
        current_password = data.get("current_password")

        if not current_password:
            return None, {"error": "É necessário inserir a senha atual para trocar a senha"}

        if not bcrypt.checkpw(
            current_password.encode("utf-8"), user["password"].encode("utf-8")
        ):
            return None, {"error": "Senha atual incorreta"}

        hashed = bcrypt.hashpw(
            data["password"].encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

        updated_fields["password"] = hashed

    if not updated_fields:
        return None, {"error": "Nenhum campo alterado"}

    mongo["users"].update_one({"_id": user["_id"]}, {"$set": updated_fields})

    return {"message": "Usuário atualizado com sucesso"}, None


def delete_user_service(email, data):

    user = mongo["users"].find_one({"email": email})

    if not user:
        return None, {"error": "Usuário não encontrado"}
    
    if user.get("auth_provider") == "google":
        mongo["users"].delete_one({"_id": user["_id"]})
        return {"message": "Usuário deletado com sucesso"}, None
    
    
    erros = delete_schema.validate(data)
    if erros:
        return None, erros

    # valida senha
    if not bcrypt.checkpw(
        data["password"].encode("utf-8"), user["password"].encode("utf-8")
    ):
        return None, {"error": "Senha incorreta"}

    mongo["users"].delete_one({"_id": user["_id"]})

    return {"message": "Usuário deletado com sucesso"}, None


def verify_email_service(token):
    user = mongo["users"].find_one({"verification_token": token})
    if not user:
        return None, {"error": "Token inválido ou expirado"}
    if user.get("is_verified"):
        return {"message": "Conta já verificada"}, None
    user = mongo["users"].find_one({"verification_token": token})
    mongo["users"].update_one(
        {"verification_token": token},
        {"$set": {"is_verified": True}, "$unset": {"verification_token": ""}},
    )
    gevent.spawn(send_welcome_email, user["name"], user["email"]).link_exception(
        _email_error_handler
    )
    return {"message": "E-mail confirmado com sucesso"}, None
