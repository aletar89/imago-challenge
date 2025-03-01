from flask import Flask
from flask_cors import CORS
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def create_app(config=None):
    app = Flask(__name__)
    CORS(app)

    # Load configuration from environment variables
    app.config.from_mapping(
        ELASTICSEARCH_HOST=os.environ.get("ELASTICSEARCH_HOST", "http://localhost"),
        ELASTICSEARCH_PORT=int(os.environ.get("ELASTICSEARCH_PORT", 9200)),
        ELASTICSEARCH_INDEX=os.environ.get("ELASTICSEARCH_INDEX", "media"),
        ELASTICSEARCH_USER=os.environ.get("ELASTICSEARCH_USER", ""),
        ELASTICSEARCH_PASSWORD=os.environ.get("ELASTICSEARCH_PASSWORD", ""),
        IMAGE_BASE_URL=os.environ.get("IMAGE_BASE_URL", "https://example.com"),
    )

    # Override with any passed config
    if config:
        app.config.update(config)

    # Register blueprints
    from app.api.routes import api_bp, init_elasticsearch
    from app.routes import main_bp

    app.register_blueprint(api_bp)
    app.register_blueprint(main_bp)

    # Initialize Elasticsearch service
    init_elasticsearch(app)

    return app
