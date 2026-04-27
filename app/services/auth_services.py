import bcrypt
from ..extensions import mongo
from ..schemas.auth_schema import LoginSchema
from ..utils.jwt_utils import generate_token

schema = LoginSchema()

def login_service(data):
    errors = schema.validate(data)
    if errors:
        return None, errors
    
    user = mongo['users'].find_one({'email':data['email']})
    if not user:
        return None, {'error':'Credenciais inválidas'}
    
    if not bcrypt.checkpw(data['password'].encode('utf-8'), user['password'].encode('utf-8')):
        return None, {'error':'Credenciais inválidas'}

    token = generate_token(data['email'])
    return {'token': token}, None