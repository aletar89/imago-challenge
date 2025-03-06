import os

import pytest
from dotenv import load_dotenv

from app import create_app

# Load environment variables
load_dotenv()


@pytest.fixture
def client():
    """Create a Flask app and test client for all tests"""
    # Create the app with the real config from .env
    app = create_app({"TESTING": True})

    # Create test client
    return app.test_client()


def test_search_endpoint(client):
    """Test the search endpoint with real Elasticsearch"""
    # Make request with a search term that should return results
    response = client.get("/api/search?q=test&page=1&size=10")

    # Check response
    assert response.status_code == 200
    data = response.get_json()

    # Verify we get a proper response with results
    assert "total" in data
    assert "hits" in data

    # If there are hits, verify they have the expected structure
    if data["total"] > 0 and len(data["hits"]) > 0:
        hit = data["hits"][0]
        # Verify hit has expected fields
        assert "id" in hit
        assert "search_text" in hit
        assert "photographer" in hit
        assert "date" in hit
        assert "thumbnail_url" in hit
        assert "bildnummer" in hit
        # Verify image URL format
        image_base_url = os.environ.get("IMAGE_BASE_URL", "https://www.imago-images.de")
        assert hit["thumbnail_url"].startswith(image_base_url)


def test_empty_search_returns_all_results(client):
    """Test the search endpoint with empty query to verify we get all results"""
    response = client.get("/api/search?q=&page=1&size=10")

    # Check response
    assert response.status_code == 200
    data = response.get_json()

    # Verify we get a proper response
    assert "total" in data
    assert "hits" in data

    # Verify we get at least some results (assuming the ES has data)
    assert data["total"] > 0
    assert len(data["hits"]) > 0


@pytest.mark.parametrize("filter_type", ["photographer", "min_date", "max_date"])
def test_filtered_search_reduces_results(client, filter_type):
    """
    Test that applying filters reduces the number of search results.

    This test verifies that:
    1. A search without filters returns results
    2. Extracting a filter value from the first result
    3. Applying that filter reduces the number of results
    """
    # First, get all results without filtering
    unfiltered_response = client.get("/api/search?q=&page=1&size=50")
    assert unfiltered_response.status_code == 200
    unfiltered_data = unfiltered_response.get_json()

    # Skip test if no data available
    if unfiltered_data["total"] == 0 or len(unfiltered_data["hits"]) == 0:
        pytest.skip(
            f"No data available in Elasticsearch for testing {filter_type} filtering"
        )

    # Get total number of results without filtering
    unfiltered_total = unfiltered_data["total"]

    # Extract filter value from first result
    first_result = unfiltered_data["hits"][0]

    # Set filter param based on filter type
    filter_value = ""
    if filter_type == "photographer":
        filter_value = first_result["photographer"]
    elif filter_type == "min_date":
        filter_value = first_result["date"]
    elif filter_type == "max_date":
        filter_value = first_result["date"]

    # Now search with the filter applied
    filtered_response = client.get(f"/api/search?q=&{filter_type}={filter_value}")
    assert filtered_response.status_code == 200
    filtered_data = filtered_response.get_json()

    # Get total number of results with filtering
    filtered_total = filtered_data["total"]

    # Verify filter reduces results (or at least doesn't increase them)
    assert filtered_total <= unfiltered_total, (
        f"Filtering by {filter_type} should reduce or maintain result count, "
        f"but got {filtered_total} results with filter vs {unfiltered_total} without"
    )

    # If we got results, verify they match the filter
    if filtered_data["total"] > 0:
        for hit in filtered_data["hits"]:
            if filter_type == "photographer":
                assert hit["photographer"] == filter_value
            elif filter_type == "min_date":
                assert hit["date"] >= filter_value
            elif filter_type == "max_date":
                assert hit["date"] <= filter_value
