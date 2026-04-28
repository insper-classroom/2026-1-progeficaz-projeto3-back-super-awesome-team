from ..models import User
from ..extensions import mongo
from ..schemas import UserSchema
from ..utils import send_email
import bcrypt
import gevent

schema = UserSchema()

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
    
    # Envia e-mail de boas-vindas
    subject = "Bem-vindo!"
    body = f"Olá {data['name']},\n\nBem-vindo à nossa plataforma! Estamos empolgados em ter você conosco.\n\nAtenciosamente,\nFinance Group"
    gevent.spawn(send_email, subject, body, data['email']).link_exception(_email_error_handler)
    
    return {'message': 'OK ✅'}, None