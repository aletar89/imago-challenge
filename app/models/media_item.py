from dataclasses import dataclass, field
from typing import Any


@dataclass
class MediaItem:
    """Represents a media item returned from search results."""

    id: str
    title: str = ""
    description: str = ""
    photographer: str = ""  # Corresponds to 'fotografen' in original data
    date: str = ""  # Corresponds to 'datum' in original data
    thumbnail_url: str = ""

    # Store all other fields in this dictionary
    additional_data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert the dataclass to a dictionary for JSON serialization."""
        result = {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "photographer": self.photographer,
            "date": self.date,
            "thumbnail_url": self.thumbnail_url,
        }

        # Add all additional data
        result.update(self.additional_data)

        return result
