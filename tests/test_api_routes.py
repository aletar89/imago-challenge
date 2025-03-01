import pytest
from unittest.mock import patch, MagicMock
from app import create_app


@pytest.fixture
def app():
    """Create a Flask app for testing with mock ElasticsearchService"""
    with patch("app.api.routes.ElasticsearchService") as mock_es_service_class:
        # Create a mock instance
        mock_es_service = MagicMock()
        mock_es_service_class.return_value = mock_es_service

        # Store the mock service for use in tests
        test_config = {
            "TESTING": True,
            "ELASTICSEARCH_HOST": "test-host",
            "ELASTICSEARCH_PORT": 9200,
            "ELASTICSEARCH_INDEX": "test-index",
            "ELASTICSEARCH_USER": "test-user",
            "ELASTICSEARCH_PASSWORD": "test-pass",
            "IMAGE_BASE_URL": "https://test-images.com",
        }
        app = create_app(test_config)
        app.mock_es_service = mock_es_service

        yield app


@pytest.fixture
def client(app):
    """Create a test client for the app"""
    return app.test_client()


def test_search_endpoint(app, client):
    """Test the search endpoint"""
    # Setup mock response
    app.mock_es_service.search.return_value = {
        "total": 2,
        "hits": [
            {
                "id": "1",
                "bildnummer": "123456",
                "datum": "2023-01-01",
                "suchtext": "Test image 1",
                "fotografen": "Test Photographer",
                "hoehe": 1000,
                "breite": 2000,
                "db": "st",
                "score": 1.0,
            },
            {
                "id": "2",
                "bildnummer": "789012",
                "datum": "2023-01-02",
                "suchtext": "Test image 2",
                "fotografen": "Another Photographer",
                "hoehe": 1200,
                "breite": 1800,
                "db": "sp",
                "score": 0.8,
            },
        ],
    }

    # Make request
    response = client.get("/api/search?q=test&page=1&size=10")

    # Check response
    assert response.status_code == 200
    data = response.get_json()

    # Verify data structure
    assert data["total"] == 2
    assert len(data["hits"]) == 2

    # Verify image URLs were constructed with test base URL
    assert (
        data["hits"][0]["image_url"]
        == "https://test-images.com/bild/st/0000123456/s.jpg"
    )
    assert (
        data["hits"][1]["image_url"]
        == "https://test-images.com/bild/sp/0000789012/s.jpg"
    )

    # Verify search was called with correct parameters
    app.mock_es_service.search.assert_called_once_with("test", 1, 10)


def test_get_media_endpoint_found(app, client):
    """Test getting a specific media item when it exists"""
    # Setup mock response
    app.mock_es_service.get_by_id.return_value = {
        "id": "1",
        "bildnummer": "123456",
        "datum": "2023-01-01",
        "suchtext": "Test image 1",
        "fotografen": "Test Photographer",
        "hoehe": 1000,
        "breite": 2000,
        "db": "st",
        "score": 1.0,
    }

    # Make request
    response = client.get("/api/media/123456")

    # Check response
    assert response.status_code == 200
    data = response.get_json()

    # Verify data
    assert data["id"] == "1"
    assert data["bildnummer"] == "123456"
    assert data["image_url"] == "https://test-images.com/bild/st/0000123456/s.jpg"

    # Verify get_by_id was called with correct parameters
    app.mock_es_service.get_by_id.assert_called_once_with("123456")


def test_get_media_endpoint_not_found(app, client):
    """Test getting a specific media item when it doesn't exist"""
    # Setup mock response
    app.mock_es_service.get_by_id.return_value = None

    # Make request
    response = client.get("/api/media/nonexistent")

    # Check response
    assert response.status_code == 404
    data = response.get_json()
    assert "error" in data
    assert data["error"] == "Media not found"


def test_filter_endpoint(app, client):
    """Test the filter endpoint"""
    # Setup mock response
    app.mock_es_service.filter.return_value = {
        "total": 1,
        "hits": [
            {
                "id": "1",
                "bildnummer": "123456",
                "datum": "2023-01-01",
                "suchtext": "Test image 1",
                "fotografen": "Test Photographer",
                "hoehe": 1000,
                "breite": 2000,
                "db": "st",
                "score": 1.0,
            }
        ],
    }

    # Make request with filter parameters
    response = client.get(
        "/api/filter?photographer=Test%20Photographer&min_date=2023-01-01&page=2&size=5"
    )

    # Check response
    assert response.status_code == 200
    data = response.get_json()

    # Verify data structure
    assert data["total"] == 1
    assert len(data["hits"]) == 1
    assert (
        data["hits"][0]["image_url"]
        == "https://test-images.com/bild/st/0000123456/s.jpg"
    )

    # Verify filter was called with correct parameters
    app.mock_es_service.filter.assert_called_once()
    args, kwargs = app.mock_es_service.filter.call_args

    # Check that filters were passed correctly
    filters = args[0]
    assert filters["photographer"] == "Test Photographer"
    assert filters["min_date"] == "2023-01-01"

    # Check pagination parameters
    assert args[1] == 2  # page
    assert args[2] == 5  # size
