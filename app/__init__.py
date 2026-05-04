from dotenv import load_dotenv

load_dotenv()

import os
from flask import Flask, request
from .extensions import mongo
from .routes import user_bp
from .routes import auth_bp
from .routes import group_bp
from .routes import bill_bp
from .routes import pendency_bp
from .routes import expense_bp
from .routes import goal_bp


DEFAULT_CORS_ORIGINS = (
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
)


def _get_allowed_origins():
    origins = os.getenv("CORS_ORIGINS")
    if not origins:
        return set(DEFAULT_CORS_ORIGINS)
    return {
        origin.strip().rstrip("/") for origin in origins.split(",") if origin.strip()
    }


def _get_allowed_origin(origin):
    if not origin:
        return None

    allowed_origins = _get_allowed_origins()
    normalized_origin = origin.rstrip("/")
    if "*" in allowed_origins:
        return origin
    if normalized_origin in allowed_origins:
        return origin
    return None


def create_app():
    app = Flask(__name__)
    app.secret_key = os.getenv("SECRET_KEY", "dev-secret")

    @app.after_request
    def add_cors_headers(response):
        allowed_origin = _get_allowed_origin(request.headers.get("Origin"))
        if not allowed_origin:
            return response

        response.headers["Access-Control-Allow-Origin"] = allowed_origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        response.headers["Access-Control-Allow-Methods"] = (
            "GET, POST, PUT, PATCH, DELETE, OPTIONS"
        )
        response.headers.add("Vary", "Origin")
        return response

    app.register_blueprint(user_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(group_bp)
    app.register_blueprint(bill_bp)
    app.register_blueprint(pendency_bp)
    app.register_blueprint(expense_bp)
    app.register_blueprint(goal_bp)

    return app
