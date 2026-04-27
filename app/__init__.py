from flask import Flask
from dotenv import load_dotenv
from .extensions import mongo
from .routes.user import user_bp
from .routes.auth import auth_bp

load_dotenv()

def create_app():
    app = Flask(__name__)

    app.register_blueprint(user_bp)
    app.register_blueprint(auth_bp)

    return app