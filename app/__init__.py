"""Flask application package for the media search application.

This package contains the main application factory and related components.
"""

import os
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
from app.services.elasticsearch_service import init_elasticsearch_service

# Load environment variables from .env file
load_dotenv()


def create_app(config=None):
    """Create and configure the Flask application.

    Args:
        config: Optional configuration dictionary to override defaults

    Returns:
        Configured Flask application instance
    """
    app = Flask(__name__)
    CORS(app)

    # Override with any passed config
    if config:
        app.config.update(config)

    # Import blueprints here to avoid circular imports
    # Note: Flask applications often use inside-function imports as part of the
    # Application Factory pattern to prevent circular dependencies. Blueprints may
    # import from app, so importing them at the top level would create circular imports.
    from app.api.routes import api_bp  # pylint: disable=import-outside-toplevel
    from app.routes import main_bp  # pylint: disable=import-outside-toplevel

    app.register_blueprint(api_bp)
    app.register_blueprint(main_bp)

    # Store the Elasticsearch service in the app context
    with app.app_context():
        app.elasticsearch = init_elasticsearch_service()

    return app
