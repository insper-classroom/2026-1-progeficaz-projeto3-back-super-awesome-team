import jwt
import os
from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import request, jsonify

SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'dev-secret-key')

def generate_token(email):
    payload = {
        'sub': email,
        'iat': datetime.now(timezone.utc),
        'exp': datetime.now(timezone.utc) + timedelta(hours=24)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')

def decode_token(token):
    return jwt.decode(token, SECRET_KEY, algorithms=['HS256'])

def jwt_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Token ausente ou inválido'}), 401
        token = auth_header.split(' ')[1]
        try:
            payload = decode_token(token)
            request.current_user = payload['sub']
        except jwt.ExpiredSignatureError:
            return jsonify({'error':'Token expirado'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error':'Token inválido'}), 401
        return f(*args, **kwargs)
    return decorated