from ..models.user import User
from ..extensions import mongo
from ..schemas.user_schema import UserSchema
from ..utils.email_utils import enviar_email
import bcrypt

schema = UserSchema()

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
    try:
        enviar_email(subject, body, data['email'])
    except Exception as e:
        print(f"Erro ao enviar e-mail: {e}")
    
    return {'message': 'OK ✅'}, None