from flask import Flask
from dotenv import load_dotenv
from .extensions import mongo
from .routes import user_bp
from .routes import auth_bp
from .routes import group_bp

load_dotenv()

def create_app():
    app = Flask(__name__)

    app.register_blueprint(user_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(group_bp)

    return app