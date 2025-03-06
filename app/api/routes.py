"""API routes for the application.

This module defines the API endpoints for the media search functionality.
"""

from flask import Blueprint, current_app, jsonify, request

from app.services.monitoring import monitor_api

api_bp = Blueprint("api", __name__, url_prefix="/api")


def build_image_url(base_url: str, item: dict) -> str:
    """
    Build the image URL for a media item

    Args:
        base_url: Base URL for images
        item: Media item data

    Returns:
        The image URL
    """
    if "bildnummer" not in item or "db" not in item:
        return ""

    # Ensure bildnummer is padded to 10 characters
    padded_bildnummer = item["bildnummer"].zfill(10)
    db = item.get("db", "st")

    # Construct the URL
    return f"{base_url}/bild/{db}/{padded_bildnummer}"


@api_bp.route("/search", methods=["GET"])
@monitor_api(endpoint="search")
def search():
    """
    Search endpoint that allows searching media by keywords with optional filtering

    Query params:
    - q: Search query string
    - page: Page number (default: 1)
    - size: Number of results per page (default: 10)

    Filter params:
    - photographer: Filter by photographer name
    - min_date/max_date: Filter by date range
    - Any other field in the document can be used as a filter
    """
    query = request.args.get("q", "")
    page = int(request.args.get("page", 1))
    size = int(request.args.get("size", 10))

    # Extract filter parameters
    filters = {}
    for key, value in request.args.items():
        if key not in ["q", "page", "size"]:
            filters[key] = value

    # Get the Elasticsearch service from the app context
    es_service = current_app.elasticsearch
    total, media_items = es_service.search(query, page, size, filters)

    # Return the results as a dictionary
    return jsonify(
        {"total": total, "hits": [media_item.to_dict() for media_item in media_items]}
    )
