"""Media fetch service abstraction.

This module provides the abstract base class for services that fetch media
items from various sources.
"""

from abc import ABC, abstractmethod
import bleach

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
        # Sanitize all string values in additional_data to prevent security issues
        for key, value in media_item.additional_data.items():
            if isinstance(value, str):
                # Clean the string, removing all HTML tags
                sanitized = bleach.clean(value, strip=True, tags=[])
                # Limit string length for additional safety
                sanitized = sanitized[:500]  # Reasonable maximum length
                media_item.additional_data[key] = sanitized
