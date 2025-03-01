from flask import Blueprint, jsonify, request, current_app, render_template
from app.services.elasticsearch_service import ElasticsearchService

api_bp = Blueprint("api", __name__, url_prefix="/api")
es_service = None


# Setup function that will be registered in the create_app function
def init_elasticsearch(app):
    global es_service
    with app.app_context():
        es_service = ElasticsearchService(
            host=app.config["ELASTICSEARCH_HOST"],
            port=app.config["ELASTICSEARCH_PORT"],
            index=app.config["ELASTICSEARCH_INDEX"],
            username=app.config["ELASTICSEARCH_USER"],
            password=app.config["ELASTICSEARCH_PASSWORD"],
            verify_certs=False,
        )


@api_bp.route("/search", methods=["GET"])
def search():
    """
    Search endpoint that allows searching media by keywords
    Query params:
    - q: Search query string
    - page: Page number (default: 1)
    - size: Number of results per page (default: 10)
    """
    query = request.args.get("q", "")
    page = int(request.args.get("page", 1))
    size = int(request.args.get("size", 10))

    results = es_service.search(query, page, size)

    # Transform results to include image URLs
    base_url = current_app.config["IMAGE_BASE_URL"]
    for hit in results["hits"]:
        hit["image_url"] = build_image_url(base_url, hit)

    return jsonify(results)


@api_bp.route("/media/<media_id>", methods=["GET"])
def get_media(media_id):
    """Get a specific media item by ID"""
    result = es_service.get_by_id(media_id)

    if not result:
        return jsonify({"error": "Media not found"}), 404

    # Add image URL to result
    base_url = current_app.config["IMAGE_BASE_URL"]
    result["image_url"] = build_image_url(base_url, result)

    return jsonify(result)


@api_bp.route("/filter", methods=["GET"])
def filter_media():
    """
    Filter endpoint that allows filtering by various fields
    Query params can include any field in the document
    - photographer: Filter by photographer name
    - min_date/max_date: Filter by date range
    - page: Page number (default: 1)
    - size: Number of results per page (default: 10)
    """
    filters = {}
    for key, value in request.args.items():
        if key not in ["page", "size"]:
            filters[key] = value

    page = int(request.args.get("page", 1))
    size = int(request.args.get("size", 10))

    results = es_service.filter(filters, page, size)

    # Transform results to include image URLs
    base_url = current_app.config["IMAGE_BASE_URL"]
    for hit in results["hits"]:
        hit["image_url"] = build_image_url(base_url, hit)

    return jsonify(results)


def build_image_url(base_url, media):
    """Build an image URL based on the media object"""
    # Get DB (default to "st" if not available)
    db = media.get("db", "st")

    # Use st/sp as mentioned in requirements if DB is "stock"
    if db == "stock":
        db = "st"

    # Get media ID and pad to 10 chars
    media_id = str(media.get("bildnummer", ""))
    media_id = media_id.zfill(10)

    # Construct URL
    return f"{base_url}/bild/{db}/{media_id}/s.jpg"
