"""Media fetch service abstraction.

This module provides the abstract base class for services that fetch media
items from various sources.
"""

from abc import ABC, abstractmethod

from app.models.media_item import MediaItem


class MediaFetchService(ABC):
    """Abstract base class for services that fetch media items from various sources"""

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
        # Fetch media items from the data source
        total, items = self.fetch_media_items(query, page, size, filters)

        # Normalize each item
        for item in items:
            self.normalize_media_item(item)

        return total, items

    @abstractmethod
    def fetch_media_items(
        self, query: str, page: int, size: int, filters: dict[str, str] | None
    ) -> tuple[int, list[MediaItem]]:
        """Fetch media items from the data source.

        Args:
            query: The search query
            page: Page number (starting from 1)
            size: Number of results per page
            filters: Optional dictionary with filter criteria

        Returns:
            Tuple containing (total_count, list of MediaItem objects)
        """
        # This is an abstract method, no implementation needed

    @staticmethod
    def normalize_media_item(media_item: MediaItem) -> None:
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
