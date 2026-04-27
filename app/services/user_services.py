from ..models.user import User
from ..extensions import mongo
from ..schemas.user_schema import UserSchema
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
    return {'message': 'OK ✅'}, None