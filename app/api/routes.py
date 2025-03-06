from flask import Blueprint, jsonify, request, current_app
import os

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
    results = es_service.search(query, page, size, filters)

    # Transform results to include image URLs
    base_url = os.environ.get("IMAGE_BASE_URL", "https://example.com")
    for hit in results["hits"]:
        hit["image_url"] = build_image_url(base_url, hit)

    return jsonify(results)


@api_bp.route("/media/<media_id>", methods=["GET"])
def get_media(media_id):
    """Get a specific media item by ID"""
    try:
        # Get the Elasticsearch service from the app context
        es_service = current_app.elasticsearch
        result = es_service.get_by_id(media_id)
        return jsonify(result)
    except Exception:
        return jsonify({"error": "Media not found"}), 404
