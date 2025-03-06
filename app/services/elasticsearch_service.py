import logging
import os
from typing import Any, Optional, List, Tuple

from elasticsearch import Elasticsearch

from app.models.media_item import MediaItem


class ElasticsearchService:
    """Service for interacting with Elasticsearch"""

    def __init__(
        self,
        host: str,
        port: int,
        index: str,
        username: str = "",
        password: str = "",
        verify_certs: bool = True,
    ) -> None:
        """
        Initialize the Elasticsearch service

        Args:
            host: Elasticsearch host
            port: Elasticsearch port
            index: Index name to use
            username: Username for authentication
            password: Password for authentication
            verify_certs: Whether to verify SSL certificates
        """
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
            verify_certs=verify_certs,
        )
        logging.info(f"Connected to Elasticsearch at {host}:{port}")

    def search(
        self,
        query: str,
        page: int = 1,
        size: int = 10,
        filters: dict[str, str] | None = None,
    ) -> tuple[int, list[MediaItem]]:
        """Search for media content with optional filtering.

        Args:
            query: The search query
            page: Page number (starting from 1)
            size: Number of results per page
            filters: Optional dictionary with filter criteria

        Returns:
            Tuple containing (total_count, list of MediaItem objects)
        """
        # Calculate from value for pagination
        from_value = (page - 1) * size

        # Build the query
        if query:
            match_query = {
                "multi_match": {
                    "query": query,
                    "fields": ["suchtext", "fotografen"],
                }
            }
        else:
            match_query = {"match_all": {}}

        # If we have filters, build a filtered query
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

        # Execute the search
        response = self.client.search(
            index=self.index,
            query=search_query,
            from_=from_value,
            size=size,
        )

        # Process the results
        return self._process_search_results(response)

    def _process_search_results(self, response: Any) -> tuple[int, list[MediaItem]]:
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

        results: list[MediaItem] = []
        for hit in hits_list:
            source = hit.get("_source", {})

            # Create a MediaItem instance
            media_item = MediaItem(
                id=hit.get("_id", ""),
                search_text=source.get("suchtext", ""),
                photographer=source.get("fotografen", ""),
                date=source.get("datum", ""),
                score=hit.get("_score", 0),
            )

            # Add all other fields to additional_data
            for key, value in source.items():
                if key not in ["suchtext", "fotografen", "datum"]:
                    media_item.additional_data[key] = value

            # Normalize the data
            self._normalize_media_item(media_item)

            # Add thumbnail URL
            bildnummer = media_item.additional_data.get("bildnummer", "")
            db = media_item.additional_data.get("db", "")
            if bildnummer and db:
                media_item.thumbnail_url = self._build_thumbnail_url(bildnummer, db)

            results.append(media_item)

        return total, results

    @staticmethod
    def _normalize_media_item(media_item: MediaItem) -> None:
        """Normalize media item fields.

        Args:
            media_item: The media item to normalize
        """
        # Set default values for missing fields in additional_data
        defaults = {
            "bildnummer": "",
            "hoehe": 0,
            "breite": 0,
            "db": "st",
        }

        for field, default_value in defaults.items():
            if field not in media_item.additional_data:
                media_item.additional_data[field] = default_value

        # Convert bildnummer to string if it's an integer
        bildnummer = media_item.additional_data.get("bildnummer")
        if isinstance(bildnummer, int):
            media_item.additional_data["bildnummer"] = str(bildnummer)

        # Convert hoehe and breite to integers if they're strings
        for field in ["hoehe", "breite"]:
            value = media_item.additional_data.get(field)
            if isinstance(value, str) and value.isdigit():
                media_item.additional_data[field] = int(value)

    @staticmethod
    def _build_thumbnail_url(bildnummer: str, db: str) -> str:
        """Build the thumbnail URL for a media item.

        Args:
            bildnummer: The bildnummer of the media item
            db: The database identifier

        Returns:
            The thumbnail URL
        """
        # Ensure bildnummer is padded to 10 characters
        padded_bildnummer = bildnummer.zfill(10)

        # Get base URL from environment variables with default
        base_url = os.environ.get("IMAGE_BASE_URL")

        # Construct the URL using the formula: IMAGE_BASE_URL + "/bild/" + DB + "/" + MEDIA_ID
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
        host=host,
        port=port,
        index=index,
        username=username,
        password=password,
        verify_certs=False,
    )
