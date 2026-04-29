from dotenv import load_dotenv
load_dotenv()

from flask import Flask
from .extensions import mongo
from .routes import user_bp
from .routes import auth_bp
from .routes import group_bp
from .routes import bill_bp
from .routes import pendency_bp

def create_app():
    app = Flask(__name__)

    app.register_blueprint(user_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(group_bp)
    app.register_blueprint(bill_bp)
    app.register_blueprint(pendency_bp)

    return app