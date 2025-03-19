"""Elasticsearch service implementation.

This module provides the ElasticsearchService class which handles interactions
with the Elasticsearch backend for media content retrieval.
"""

import logging
import os
from typing import Any

from elasticsearch import Elasticsearch

from app.models.media_item import MediaItem
from app.services.media_fetch_service import MediaFetchService


class ElasticsearchService(MediaFetchService):
    """Service for interacting with Elasticsearch"""

    def __init__(
        self,
        connection_config: dict[str, Any],
        index: str,
    ) -> None:
        """
        Initialize the Elasticsearch service

        Args:
            connection_config: Dictionary containing connection parameters
                (host, port, username, password, ssl_options)
            index: Index name to use
        """
        host = connection_config.get("host", "localhost")
        port = connection_config.get("port", 9200)
        username = connection_config.get("username", "")
        password = connection_config.get("password", "")
        ssl_options = connection_config.get("ssl_options", {})

        # Ensure host has a scheme (http:// or https://)
        if not host.startswith("http://") and not host.startswith("https://"):
            host = f"https://{host}"

        self.index = index

        auth = None
        if username and password:
            auth = (username, password)

        self.client = Elasticsearch(
            hosts=[f"{host}:{port}"],
            basic_auth=auth,
            verify_certs=ssl_options.get("verify_certs", False),
        )
        logging.info("Connected to Elasticsearch at %s:%s", host, port)

    def get_unique_photographers(self, size: int = 1000) -> list[str]:
        """Fetch a list of unique photographers from Elasticsearch.

        Args:
            size: Maximum number of unique values to return (default: 1000)

        Returns:
            A list of unique photographer names
        """
        # Execute the search with aggregations
        response = self.client.search(
            index=self.index,
            size=0,  # Don't return any documents, just aggregations
            aggs={
                "unique_photographers": {
                    "terms": {
                        "field": "fotografen",
                        "size": size,
                        "order": {"_key": "asc"},  # Sort alphabetically
                    }
                }
            },
        )

        # Process aggregation results
        if hasattr(response, "body"):
            response_body = response.body
        else:
            response_body = response

        buckets = (
            response_body.get("aggregations", {})
            .get("unique_photographers", {})
            .get("buckets", [])
        )
        photographers = [bucket.get("key") for bucket in buckets if bucket.get("key")]

        return photographers

    def fetch_media_items(
        self, query: str, page: int, size: int, filters: dict[str, str] | None
    ) -> tuple[int, list[MediaItem]]:
        """Fetch media items from Elasticsearch.

        Args:
            query: The search query
            page: Page number (starting from 1)
            size: Number of results per page
            filters: Optional dictionary with filter criteria

        Returns:
            Tuple containing (total_count, list of MediaItem objects)
        """
        # Build the Elasticsearch query
        es_query = self._build_elasticsearch_query(query, filters)

        # Calculate from value for pagination
        from_value = (page - 1) * size

        # Execute the search
        response = self.client.search(
            index=self.index,
            query=es_query,
            from_=from_value,
            size=size,
        )

        # Process the results
        return self.process_search_results(response)

    def _build_elasticsearch_query(
        self, query: str, filters: dict[str, str] | None
    ) -> dict[str, Any]:
        """Build an Elasticsearch query with optional filters.

        Args:
            query: The search query
            filters: Optional dictionary with filter criteria

        Returns:
            Elasticsearch query dictionary
        """
        # Build the base query
        if query:
            match_query = {
                "multi_match": {
                    "query": query,
                    "fields": ["suchtext", "description", "title"],
                }
            }
        else:
            # Fallback to match all if no query is provided
            match_query = {"match_all": {}}

        if filters and len(filters) > 0:
            filter_conditions: list[dict[str, Any]] = []

            if "photographer" in filters:
                filter_conditions.append(
                    {"term": {"fotografen": filters["photographer"]}}
                )

            if "min_date" in filters:
                filter_conditions.append(
                    {"range": {"datum": {"gte": filters["min_date"]}}}
                )

            if "max_date" in filters:
                filter_conditions.append(
                    {"range": {"datum": {"lte": filters["max_date"]}}}
                )

            # Add any additional custom filters
            for key, value in filters.items():
                if key not in ["photographer", "min_date", "max_date"]:
                    filter_conditions.append({"term": {key: value}})

            # Combine match query with filters
            search_query: dict[str, Any] = {
                "bool": {"must": match_query, "filter": filter_conditions}
            }
        else:
            search_query = match_query

        return search_query

    def process_search_results(self, response: Any) -> tuple[int, list[MediaItem]]:
        """Process Elasticsearch search results.

        Args:
            response: Elasticsearch response object or dict

        Returns:
            Tuple containing (total_count, list of MediaItem objects)
        """
        # Handle both dict and ObjectApiResponse types
        if hasattr(response, "body"):
            response_body = response.body
        else:
            response_body = response

        hits = response_body.get("hits", {})
        total = hits.get("total", {}).get("value", 0)
        hits_list = hits.get("hits", [])

        return total, [self.convert_hit_to_media_item(hit) for hit in hits_list]

    def convert_hit_to_media_item(self, hit: dict[str, Any]) -> MediaItem:
        """Convert an Elasticsearch hit to a MediaItem.

        Args:
            hit: Elasticsearch hit dictionary

        Returns:
            Populated MediaItem
        """
        source = hit.get("_source", {})
        suchtext = source.get("suchtext", "")

        # Set title and description with fallback to suchtext
        title = source.get("title", suchtext[:50].strip())
        description = source.get("description", suchtext)

        # Create a MediaItem instance
        media_item = MediaItem(
            id=hit.get("_id", ""),
            title=title,
            description=description,
            photographer=source.get("fotografen", ""),
            date=source.get("datum", ""),
            additional_data={
                "bildnummer": "",
                "hoehe": 0,
                "breite": 0,
                "db": "st",
                "score": hit.get("_score", 0),  # Move score to additional_data
            },  # default values
        )

        # Add all other fields to additional_data
        for key, value in source.items():
            if key not in ["title", "description", "fotografen", "datum"]:
                media_item.additional_data[key] = value

        # Add thumbnail URL
        bildnummer = media_item.additional_data.get("bildnummer", "")
        db = media_item.additional_data.get("db", "")
        if bildnummer and db:
            media_item.thumbnail_url = self.build_thumbnail_url(bildnummer, db)

        return media_item

    @staticmethod
    def build_thumbnail_url(bildnummer: str, db: str) -> str:
        """Build the thumbnail URL for a media item.

        Args:
            bildnummer: The bildnummer of the media item
            db: The database identifier

        Returns:
            The thumbnail URL
        """
        # Ensure bildnummer is padded to 10 characters
        padded_bildnummer = bildnummer.zfill(10)
        base_url = os.environ.get("IMAGE_BASE_URL")
        return f"{base_url}/bild/{db}/{padded_bildnummer}/s.jpg"


def init_elasticsearch_service() -> ElasticsearchService:
    """
    Initialize the Elasticsearch service using environment variables.
    This should be called once during application startup.

    Returns:
        ElasticsearchService: The initialized Elasticsearch service
    """
    # Load configuration from environment variables
    host = os.environ.get("ELASTICSEARCH_HOST", "http://localhost")
    port = int(os.environ.get("ELASTICSEARCH_PORT", "9200"))
    index = os.environ.get("ELASTICSEARCH_INDEX", "media")
    username = os.environ.get("ELASTICSEARCH_USER", "")
    password = os.environ.get("ELASTICSEARCH_PASSWORD", "")

    # Initialize the service
    return ElasticsearchService(
        connection_config={
            "host": host,
            "port": port,
            "username": username,
            "password": password,
            "ssl_options": {},
        },
        index=index,
    )
