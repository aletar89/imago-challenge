"""API routes for the application.

This module defines the API endpoints for the media search functionality.
"""

from datetime import datetime
import logging
from flask import Blueprint, current_app, jsonify, request
import bleach

from app.services.monitoring import monitor_api

api_bp = Blueprint("api", __name__, url_prefix="/api")


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
    """
    query = request.args.get("q", "")
    page = int(request.args.get("page", 1))
    size = int(request.args.get("size", 10))
    size = min(size, 100)

    filters = {}
    if "photographer" in request.args:
        filters["photographer"] = bleach.clean(
            request.args.get("photographer", ""), strip=True, tags=[]
        )
    if "min_date" in request.args:
        min_date = request.args.get("min_date", "")
        try:
            datetime.fromisoformat(min_date)
            filters["min_date"] = min_date
        except ValueError:
            logging.error("Invalid min_date format: %s", min_date)
    if "max_date" in request.args:
        max_date = request.args.get("max_date", "")
        try:
            datetime.fromisoformat(max_date)
            filters["max_date"] = max_date
        except ValueError:
            logging.error("Invalid max_date format: %s", max_date)

    # Get the Elasticsearch service from the app context
    es_service = current_app.elasticsearch
    try:
        total, media_items = es_service.search(query, page, size, filters)
    except Exception as e:  # pylint: disable=broad-exception-caught
        logging.error("Error searching Elasticsearch: %s", e)
        return jsonify({"error": str(e)}), 500

    # Return the results as a dictionary
    return jsonify(
        {"total": total, "hits": [media_item.to_dict() for media_item in media_items]}
    )
