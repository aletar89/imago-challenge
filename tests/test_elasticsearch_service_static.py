import copy
import os

from app.services.elasticsearch_service import ElasticsearchService

# Tests for the _normalize_item static method


def test_normalize_item_with_empty_dict():
    """Test normalizing an empty item."""
    item = {}
    ElasticsearchService._normalize_item(item)

    # Check that all default fields are set
    assert item["bildnummer"] == ""
    assert item["datum"] == ""
    assert item["suchtext"] == ""
    assert item["fotografen"] == ""
    assert item["hoehe"] == 0
    assert item["breite"] == 0
    assert item["db"] == "st"


def test_normalize_item_with_existing_values():
    """Test normalizing an item with existing values."""
    item = {
        "bildnummer": "12345",
        "datum": "2023-01-01",
        "suchtext": "Test",
        "fotografen": "Photographer",
        "hoehe": 100,
        "breite": 200,
        "db": "test",
        "extra_field": "value",
    }

    # Create a copy to verify values aren't changed
    original = item.copy()

    ElasticsearchService._normalize_item(item)

    # Check that existing values are preserved
    assert item["bildnummer"] == original["bildnummer"]
    assert item["datum"] == original["datum"]
    assert item["suchtext"] == original["suchtext"]
    assert item["fotografen"] == original["fotografen"]
    assert item["hoehe"] == original["hoehe"]
    assert item["breite"] == original["breite"]
    assert item["db"] == original["db"]
    assert item["extra_field"] == original["extra_field"]


def test_normalize_item_converts_bildnummer():
    """Test that bildnummer is converted from int to string."""
    item = {"bildnummer": 12345}
    ElasticsearchService._normalize_item(item)
    assert item["bildnummer"] == "12345"
    assert isinstance(item["bildnummer"], str)


def test_normalize_item_converts_dimensions():
    """Test that hoehe and breite are converted from string to int."""
    item = {"hoehe": "100", "breite": "200"}
    ElasticsearchService._normalize_item(item)
    assert item["hoehe"] == 100
    assert item["breite"] == 200
    assert isinstance(item["hoehe"], int)
    assert isinstance(item["breite"], int)


def test_normalize_item_non_numeric_dimensions():
    """Test that non-numeric hoehe and breite are not converted."""
    item = {"hoehe": "abc", "breite": "xyz"}
    ElasticsearchService._normalize_item(item)
    assert item["hoehe"] == "abc"
    assert item["breite"] == "xyz"


def test_normalize_item_preserves_additional_fields():
    """Test that fields not in the defaults list are preserved."""
    # Create an item with standard fields and additional custom fields
    item = {
        "bildnummer": "12345",
        "custom_field1": "custom value",
        "custom_field2": 42,
        "nested_field": {"key": "value"},
        "array_field": [1, 2, 3],
    }

    # Create a copy to verify values aren't changed
    original = item.copy()

    ElasticsearchService._normalize_item(item)

    # Verify standard fields are handled correctly
    assert item["bildnummer"] == original["bildnummer"]

    # Verify all custom fields are preserved
    assert item["custom_field1"] == original["custom_field1"]
    assert item["custom_field2"] == original["custom_field2"]
    assert item["nested_field"] == original["nested_field"]
    assert item["array_field"] == original["array_field"]

    # Verify default fields were added
    assert "datum" in item
    assert "suchtext" in item
    assert "fotografen" in item
    assert "hoehe" in item
    assert "breite" in item
    assert "db" in item


def test_normalize_item_with_complex_structures():
    """Test normalizing an item with complex nested structures."""
    # Create an item with complex nested structures
    item = {
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

    original = copy.deepcopy(item)

    ElasticsearchService._normalize_item(item)

    # Verify complex structures are preserved
    assert item["complex_object"] == original["complex_object"]
    assert item["mixed_array"] == original["mixed_array"]

    # Verify standard fields are properly converted
    assert item["bildnummer"] == "98765"
    assert isinstance(item["bildnummer"], str)
    assert item["hoehe"] == 500
    assert isinstance(item["hoehe"], int)
    assert item["breite"] == "invalid"

    # Verify default fields were added
    assert "datum" in item
    assert "suchtext" in item
    assert "fotografen" in item
    assert "db" in item


# Tests for the _build_thumbnail_url static method


def test_build_thumbnail_url():
    """Test building a thumbnail URL."""
    # Set environment variable for testing

    url = ElasticsearchService._build_thumbnail_url("12345", "test")
    expected = f"{os.environ['IMAGE_BASE_URL']}/bild/test/0000012345/s.jpg"
    assert url == expected
