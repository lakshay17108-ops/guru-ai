"""
Application factory for the Learning Path Generator API.

Why a factory pattern?
  - Different configs for dev/test/prod without touching code.
  - Each test can create its own isolated app instance.
  - Blueprints are registered here, keeping routes modular.
"""

import os

from flask import Flask
from flask_cors import CORS

from app.config import config_by_name


def create_app(config_name: str | None = None) -> Flask:
    """
    Create and configure the Flask application.

    Args:
        config_name: One of 'development', 'testing', 'production'.
                     Defaults to FLASK_ENV env var, or 'development'.
    """
    if config_name is None:
        config_name = os.getenv("FLASK_ENV", "development")

    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    # Enable CORS for all /api/* routes — the React dev server runs on
    # a different port (5173) and needs cross-origin access.
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # --- Register Blueprints ---
    from app.routes.learning_path import learning_path_bp
    app.register_blueprint(learning_path_bp)

    # --- Health check (useful for deployment probes) ---
    @app.route("/api/health")
    def health_check():
        return {"status": "healthy", "service": "learning-path-generator"}

    return app
