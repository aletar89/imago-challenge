from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()


def create_app(config=None):
    app = Flask(__name__)
    CORS(app)

    # Override with any passed config
    if config:
        app.config.update(config)

    # Register blueprints
    from app.api.routes import api_bp
    from app.routes import main_bp

    app.register_blueprint(api_bp)
    app.register_blueprint(main_bp)

    # Initialize Elasticsearch service
    from app.services.elasticsearch_service import init_elasticsearch_service

    # Store the Elasticsearch service in the app context
    with app.app_context():
        app.elasticsearch = init_elasticsearch_service()

    return app
