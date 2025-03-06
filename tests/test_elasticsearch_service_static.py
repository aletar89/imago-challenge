import copy
import os

from app.services.elasticsearch_service import ElasticsearchService
from app.models.media_item import MediaItem

# Tests for the _normalize_media_item static method


def test_normalize_media_item_with_empty_dict():
    """Test normalizing an empty media item."""
    media_item = MediaItem(id="test")
    ElasticsearchService._normalize_media_item(media_item)

    # Check that all default fields are set
    assert media_item.additional_data["bildnummer"] == ""
    assert media_item.additional_data["hoehe"] == 0
    assert media_item.additional_data["breite"] == 0
    assert media_item.additional_data["db"] == "st"


def test_normalize_media_item_with_existing_values():
    """Test normalizing a media item with existing values."""
    media_item = MediaItem(
        id="test",
        search_text="Test",
        photographer="Photographer",
        date="2023-01-01",
    )
    media_item.additional_data = {
        "bildnummer": "12345",
        "hoehe": 100,
        "breite": 200,
        "db": "test",
        "extra_field": "value",
    }

    # Create a copy to verify values aren't changed
    original_additional_data = copy.deepcopy(media_item.additional_data)

    ElasticsearchService._normalize_media_item(media_item)

    # Check that existing values are preserved
    assert (
        media_item.additional_data["bildnummer"]
        == original_additional_data["bildnummer"]
    )
    assert media_item.additional_data["hoehe"] == original_additional_data["hoehe"]
    assert media_item.additional_data["breite"] == original_additional_data["breite"]
    assert media_item.additional_data["db"] == original_additional_data["db"]
    assert (
        media_item.additional_data["extra_field"]
        == original_additional_data["extra_field"]
    )


def test_normalize_media_item_converts_bildnummer():
    """Test that bildnummer is converted from int to string."""
    media_item = MediaItem(id="test")
    media_item.additional_data["bildnummer"] = 12345
    ElasticsearchService._normalize_media_item(media_item)
    assert media_item.additional_data["bildnummer"] == "12345"
    assert isinstance(media_item.additional_data["bildnummer"], str)


def test_normalize_media_item_converts_dimensions():
    """Test that hoehe and breite are converted from string to int."""
    media_item = MediaItem(id="test")
    media_item.additional_data["hoehe"] = "100"
    media_item.additional_data["breite"] = "200"
    ElasticsearchService._normalize_media_item(media_item)
    assert media_item.additional_data["hoehe"] == 100
    assert media_item.additional_data["breite"] == 200
    assert isinstance(media_item.additional_data["hoehe"], int)
    assert isinstance(media_item.additional_data["breite"], int)


def test_normalize_media_item_non_numeric_dimensions():
    """Test that non-numeric hoehe and breite are not converted."""
    media_item = MediaItem(id="test")
    media_item.additional_data["hoehe"] = "abc"
    media_item.additional_data["breite"] = "xyz"
    ElasticsearchService._normalize_media_item(media_item)
    assert media_item.additional_data["hoehe"] == "abc"
    assert media_item.additional_data["breite"] == "xyz"


def test_normalize_media_item_preserves_additional_fields():
    """Test that fields not in the defaults list are preserved."""
    # Create a media item with standard fields and additional custom fields
    media_item = MediaItem(id="test")
    media_item.additional_data = {
        "bildnummer": "12345",
        "custom_field1": "custom value",
        "custom_field2": 42,
        "nested_field": {"key": "value"},
        "array_field": [1, 2, 3],
    }

    # Create a copy to verify values aren't changed
    original_additional_data = copy.deepcopy(media_item.additional_data)

    ElasticsearchService._normalize_media_item(media_item)

    # Verify standard fields are handled correctly
    assert (
        media_item.additional_data["bildnummer"]
        == original_additional_data["bildnummer"]
    )

    # Verify all custom fields are preserved
    assert (
        media_item.additional_data["custom_field1"]
        == original_additional_data["custom_field1"]
    )
    assert (
        media_item.additional_data["custom_field2"]
        == original_additional_data["custom_field2"]
    )
    assert (
        media_item.additional_data["nested_field"]
        == original_additional_data["nested_field"]
    )
    assert (
        media_item.additional_data["array_field"]
        == original_additional_data["array_field"]
    )

    # Verify default fields were added
    assert "hoehe" in media_item.additional_data
    assert "breite" in media_item.additional_data
    assert "db" in media_item.additional_data


def test_normalize_media_item_with_complex_structures():
    """Test normalizing a media item with complex nested structures."""
    # Create a media item with complex nested structures
    media_item = MediaItem(id="test")
    media_item.additional_data = {
        "complex_object": {
            "nested1": {"nested2": {"value": "deep value"}},
            "array": [{"item1": 1}, {"item2": 2}],
        },
        "mixed_array": [1, "string", {"key": "value"}, [1, 2, 3]],
        "bildnummer": 98765,  # Should be converted to string
        "hoehe": "500",  # Should be converted to int
        "breite": "invalid",  # Should remain string
    }

    # Create a deep copy to verify nested structures aren't changed
    original_additional_data = copy.deepcopy(media_item.additional_data)

    ElasticsearchService._normalize_media_item(media_item)

    # Verify complex structures are preserved
    assert (
        media_item.additional_data["complex_object"]
        == original_additional_data["complex_object"]
    )
    assert (
        media_item.additional_data["mixed_array"]
        == original_additional_data["mixed_array"]
    )

    # Verify standard fields are properly converted
    assert media_item.additional_data["bildnummer"] == "98765"
    assert isinstance(media_item.additional_data["bildnummer"], str)
    assert media_item.additional_data["hoehe"] == 500
    assert isinstance(media_item.additional_data["hoehe"], int)
    assert media_item.additional_data["breite"] == "invalid"

    # Verify default fields were added
    assert "db" in media_item.additional_data


# Tests for the _build_thumbnail_url static method


def test_build_thumbnail_url():
    """Test building a thumbnail URL."""
    # Set environment variable for testing
    os.environ["IMAGE_BASE_URL"] = "https://test.example.com"

    url = ElasticsearchService._build_thumbnail_url("12345", "test")
    expected = "https://test.example.com/bild/test/0000012345/s.jpg"
    assert url == expected
