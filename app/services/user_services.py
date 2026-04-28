from ..models import User
from ..extensions import mongo
from ..schemas import UserSchema, UpdateUserSchema
from ..utils import send_email
from bson import ObjectId

import bcrypt
import gevent

schema = UserSchema()
update_schema = UpdateUserSchema()

def _email_error_handler(greenlet):
    print(f'Erro ao enviar e-mail: {greenlet.exception}')

def create_user_service(data):
    erros = schema.validate(data)
    if erros:
        return None, erros

    existing = mongo['users'].find_one({'email': data['email']})
    if existing:
        return None, {'error': 'email já cadastrado'}

    hashed = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    user = User(data["name"], data["email"], hashed)
    mongo['users'].insert_one(user.to_dictionary())
    
    subject = "Bem-vindo!"
    body = f"Olá {data['name']},\n\nBem-vindo à nossa plataforma! Estamos empolgados em ter você conosco.\n\nAtenciosamente,\nFinance Group"
    gevent.spawn(send_email, subject, body, data['email']).link_exception(_email_error_handler)
    
    return {'message': 'OK ✅'}, None

def update_user_service(user_id, data):
    erros = update_schema.validate(data)
    if erros:
        return None, erros
    try:
        oid = ObjectId(user_id)
    except Exception:
        return None, {"error": "ID inválido"}

    user = mongo['users'].find_one({"_id": oid})

    if not user:
        return None, {"error": "Usuário não encontrado"}
    
    updated_fields = {}

    if 'name' in data:
        updated_fields['name'] = data['name']

    if "password" in data:

        current_password = data.get("current_password")

        if not current_password:
            return None, {"error": "Current password is required to set a new password"}

        if not bcrypt.checkpw(current_password.encode('utf-8'), user['password'].encode('utf-8')):
            return None, {"error": "Current password is incorrect"}


        hashed = bcrypt.hashpw(data["password"].encode('utf-8'), bcrypt.gensalt() ).decode('utf-8')
        updated_fields['password'] = hashed

    if not updated_fields:
        return None, {"error": "Nenhum campo alterado"}
    
    mongo["users"].update_one( {"_id": oid}, {"$set": updated_fields} )

    return {"message": "Usuário atualizado com sucesso"}, None