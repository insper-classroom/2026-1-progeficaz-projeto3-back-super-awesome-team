from flask import Flask
from .extensions import mongo
from .routes.user import user_bp

def create_app():
    app = Flask(__name__)

    #registro das rotas de usuario
    app.register_blueprint(user_bp)

    return app