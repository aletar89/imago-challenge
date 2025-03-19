"""Tests for the API routes of the application."""

from unittest.mock import patch
import pytest
from dotenv import load_dotenv

from app import create_app

# Load environment variables
load_dotenv()


@pytest.fixture(name="app_client")
def fixture_app_client():
    """Create a Flask app and test client for all tests"""
    # Create the app with the real config from .env
    app = create_app({"TESTING": True})

    # Create test client
    return app.test_client()


def test_search_endpoint(app_client):
    """Test the search endpoint with real Elasticsearch"""
    # Make request with a search term that should return results
    response = app_client.get("/api/search?q=test&page=1&size=10")

    # Check response
    assert response.status_code == 200
    data = response.get_json()

    # Verify we get a proper response with results
    assert data["total"] > 0
    assert len(data["hits"]) == 10

    hit = data["hits"][0]
    # Verify hit has expected fields
    assert "id" in hit
    assert "title" in hit
    assert "description" in hit
    assert "photographer" in hit
    assert "date" in hit
    assert "thumbnail_url" in hit


def test_empty_search_returns_all_results(app_client):
    """Test the search endpoint with empty query to verify we get all results"""

    search_response = app_client.get("/api/search?q=test&page=1&size=10")
    assert search_response.status_code == 200
    search_data = search_response.get_json()

    all_response = app_client.get("/api/search?q=&page=1&size=10")

    # Check response
    assert all_response.status_code == 200
    all_data = all_response.get_json()

    # Verify we get at least some results (assuming the ES has data)
    assert all_data["total"] > search_data["total"]
    assert len(all_data["hits"]) == 10


@pytest.mark.parametrize("filter_type", ["photographer", "min_date", "max_date"])
def test_filtered_search_reduces_results(app_client, filter_type):
    """
    Test that applying filters reduces the number of search results.

    This test verifies that:
    1. A search without filters returns results
    2. Extracting a filter value from the first result
    3. Applying that filter reduces the number of results
    """
    # First, get all results without filtering
    unfiltered_response = app_client.get("/api/search?q=&page=1&size=50")
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
    elif filter_type in ("min_date", "max_date"):
        filter_value = first_result["date"]

    # Now search with the filter applied
    filtered_response = app_client.get(f"/api/search?q=&{filter_type}={filter_value}")
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


def test_pagination_works_correctly(app_client):
    """Test that pagination parameters work correctly."""
    # Get first page with 5 results
    response_page1 = app_client.get("/api/search?q=&page=1&size=5")
    assert response_page1.status_code == 200
    data_page1 = response_page1.get_json()

    # Get second page with 5 results
    response_page2 = app_client.get("/api/search?q=&page=2&size=5")
    assert response_page2.status_code == 200
    data_page2 = response_page2.get_json()

    # Verify both pages return correct number of results
    assert len(data_page1["hits"]) == 5
    assert len(data_page2["hits"]) == 5

    # Verify the pages contain different items
    page1_ids = [item["id"] for item in data_page1["hits"]]
    page2_ids = [item["id"] for item in data_page2["hits"]]
    assert not set(page1_ids).intersection(set(page2_ids))


def test_combined_filters(app_client):
    """Test search with multiple filters applied simultaneously."""
    # First get all results count
    all_response = app_client.get("/api/search?q=&page=1&size=1")
    all_data = all_response.get_json()
    photographer = all_data["hits"][0]["photographer"]
    date = all_data["hits"][0]["date"]

    # Get photographer filter only
    photo_response = app_client.get(
        f"/api/search?q=&photographer={photographer}&page=1&size=1"
    )
    photo_data = photo_response.get_json()

    # Get date filter only
    date_response = app_client.get(f"/api/search?q=&min_date={date}&page=1&size=1")
    date_data = date_response.get_json()

    # Get combined filter
    combined_response = app_client.get(
        f"/api/search?q=&photographer={photographer}&min_date={date}&page=1&size=1"
    )
    combined_data = combined_response.get_json()

    # Combined filter should return fewer or equal results than individual filters
    assert combined_data["total"] <= photo_data["total"]
    assert combined_data["total"] <= date_data["total"]


def test_invalid_pagination_params(app_client):
    """Test handling of invalid pagination parameters."""
    # Test negative page number
    response = app_client.get("/api/search?q=test&page=-1&size=10")
    assert response.status_code == 500

    # Test excessive size (should be capped at 100)
    response = app_client.get("/api/search?q=test&page=1&size=500")
    assert response.status_code == 200
    data = response.get_json()
    assert len(data["hits"]) <= 100  # Size should be capped at 100


def test_invalid_date_format(app_client):
    """Test handling of invalid date formats in filters."""
    response = app_client.get("/api/search?q=test&min_date=not-a-date")
    assert response.status_code == 200  # Should not fail but log error

    # The invalid date should be ignored, results should be the same as without filter
    control_response = app_client.get("/api/search?q=test")
    assert response.get_json()["total"] == control_response.get_json()["total"]


def test_photographers_endpoint(app_client):
    """Test the photographers endpoint."""
    response = app_client.get("/api/photographers")
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) > 0
    assert "ABACAPRESS" in data


@patch("app.services.elasticsearch_service.ElasticsearchService.fetch_media_items")
def test_elasticsearch_error_handling(mock_fetch_media_items, app_client):
    """Test that ElasticsearchService handles errors gracefully."""
    # Setup the mock to simulate an error
    mock_fetch_media_items.side_effect = Exception("Connection error")

    # Make a request that would trigger the error
    response = app_client.get("/api/search?q=test")

    # Verify the API returns an appropriate error response
    assert response.status_code == 500

    # Verify the error response contains the error message
    data = response.get_json()
    assert "error" in data
    assert "Connection error" in data["error"]


def test_boolean_query(app_client):
    """Test that simple_query_string OR functionality works correctly."""
    # Search for cat
    cat_response = app_client.get("/api/search?q=cat&page=1&size=10")
    cat_data = cat_response.get_json()
    cat_count = cat_data["total"]

    # Search for flower
    flower_response = app_client.get("/api/search?q=flower&page=1&size=10")
    flower_data = flower_response.get_json()
    flower_count = flower_data["total"]

    # Search for cat OR flower
    combined_response = app_client.get("/api/search?q=cat | flower&page=1&size=10")
    combined_data = combined_response.get_json()
    combined_count = combined_data["total"]

    # The OR query should return at least as many results as each individual query
    assert combined_count >= cat_count
    assert combined_count >= flower_count

    # In most cases, it should return at least as many results as the sum of individual queries
    # minus any overlap (but we can't strictly assert this as it depends on data)
    # Just check it's not smaller than the larger of the two
    assert combined_count >= max(cat_count, flower_count)

    # Search for cat NOT flower
    exclusion_response = app_client.get("/api/search?q=cat -flower&page=1&size=10")
    exclusion_data = exclusion_response.get_json()
    exclusion_count = exclusion_data["total"]

    # The exclusion query should return fewer results than just "cat"
    assert exclusion_count <= cat_count
