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