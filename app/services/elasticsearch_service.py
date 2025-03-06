from elasticsearch import Elasticsearch
import logging
from typing import Any, Tuple, Optional, Union, cast
from elasticsearch.helpers import bulk
from elasticsearch.exceptions import NotFoundError
import json


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

    def search(self, query: str, page: int = 1, size: int = 10) -> dict[str, Any]:
        """Search for media content.

        Args:
            query: The search query
            page: Page number (starting from 1)
            size: Number of results per page

        Returns:
            Dictionary with total count and search results
        """
        # Calculate from value for pagination
        from_value = (page - 1) * size

        # Build the query
        search_query: dict[str, Any]
        if query:
            search_query = {
                "multi_match": {
                    "query": query,
                    "fields": ["suchtext", "fotografen"],
                }
            }
        else:
            search_query = {"match_all": {}}

        # Execute the search
        response = self.client.search(
            index=self.index,
            query=search_query,
            from_=from_value,
            size=size,
        )

        # Process the results
        return self._process_search_results(response)

    def get_by_id(self, media_id: str) -> Optional[dict[str, Any]]:
        """Get media content by ID.

        Args:
            media_id: The media ID to retrieve

        Returns:
            Media item if found, None otherwise
        """
        id_query: dict[str, Any] = {"term": {"bildnummer": media_id}}

        # Execute the search
        response = self.client.search(
            index=self.index,
            query=id_query,
            size=1,
        )

        # Process the results
        results = self._process_search_results(response)

        # Return the first hit if there are any
        if results["total"] > 0:
            return results["hits"][0]
        return None

    def filter(
        self, filters: dict[str, str], page: int = 1, size: int = 10
    ) -> dict[str, Any]:
        """Filter media content by various criteria.

        Args:
            filters: Dictionary with filter criteria
            page: Page number (starting from 1)
            size: Number of results per page

        Returns:
            Dictionary with total count and filtered results
        """
        # Calculate from value for pagination
        from_value = (page - 1) * size

        # Build filter conditions
        filter_conditions: list[dict[str, Any]] = []

        if "photographer" in filters:
            filter_conditions.append({"term": {"fotografen": filters["photographer"]}})

        if "min_date" in filters:
            min_date_range: dict[str, Any] = {"datum": {"gte": filters["min_date"]}}
            filter_conditions.append({"range": min_date_range})

        if "max_date" in filters:
            max_date_range: dict[str, Any] = {"datum": {"lte": filters["max_date"]}}
            filter_conditions.append({"range": max_date_range})

        # Build the query
        filter_query: dict[str, Any] = {"bool": {"filter": filter_conditions}}

        # Execute the search
        response = self.client.search(
            index=self.index,
            query=filter_query,
            from_=from_value,
            size=size,
        )

        # Process the results
        return self._process_search_results(response)

    def _process_search_results(self, response: Any) -> dict[str, Any]:
        """Process Elasticsearch search results.

        Args:
            response: Elasticsearch response object or dict

        Returns:
            Processed search results
        """
        # Handle both dict and ObjectApiResponse types
        if hasattr(response, "body"):
            response_body = response.body
        else:
            response_body = response

        hits = response_body.get("hits", {})
        total = hits.get("total", {}).get("value", 0)
        hits_list = hits.get("hits", [])

        results = []
        for hit in hits_list:
            item = hit.get("_source", {})
            item["id"] = hit.get("_id", "")
            item["score"] = hit.get("_score", 0)

            # Normalize the item
            self._normalize_item(item)

            # Add thumbnail URL
            if "bildnummer" in item and "db" in item:
                item["thumbnail_url"] = self._build_thumbnail_url(
                    item["bildnummer"], item["db"]
                )

            results.append(item)

        return {"total": total, "hits": results}

    def _normalize_item(self, item: dict[str, Any]) -> None:
        """Normalize item fields.

        Args:
            item: The item to normalize
        """
        # Set default values for missing fields
        defaults = {
            "bildnummer": "",
            "datum": "",
            "suchtext": "",
            "fotografen": "",
            "hoehe": 0,
            "breite": 0,
            "db": "st",
        }

        for field, default_value in defaults.items():
            if field not in item:
                item[field] = default_value

        # Convert bildnummer to string if it's an integer
        if isinstance(item["bildnummer"], int):
            item["bildnummer"] = str(item["bildnummer"])

        # Convert hoehe and breite to integers if they're strings
        for field in ["hoehe", "breite"]:
            if isinstance(item[field], str) and item[field].isdigit():
                item[field] = int(item[field])

    def _build_thumbnail_url(self, bildnummer: str, db: str) -> str:
        """Build the thumbnail URL for a media item.

        Args:
            bildnummer: The bildnummer of the media item
            db: The database identifier

        Returns:
            The thumbnail URL
        """
        return f"https://www.swissdoxarchives.ch/smartfolder/thumbview/thumbnail?bildnummer={bildnummer}&db={db}"
