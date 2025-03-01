import pytest
from unittest.mock import patch, MagicMock
from app.services.elasticsearch_service import ElasticsearchService


@pytest.fixture
def mock_es_client():
    """Fixture for mocking the Elasticsearch client"""
    with patch("elasticsearch.Elasticsearch") as mock_es:
        # Create a mock instance
        mock_instance = MagicMock()
        mock_es.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def es_service(mock_es_client):
    """Fixture for creating an ElasticsearchService with a mocked client"""
    with patch.object(ElasticsearchService, "__init__", return_value=None):
        service = ElasticsearchService(
            host="test-host",
            port=9200,
            index="test-index",
            username="test-user",
            password="test-pass",
            verify_certs=False,
        )
        service.index = "test-index"
        service.client = mock_es_client
        return service


def test_search_empty_query(es_service, mock_es_client):
    """Test searching with an empty query"""
    # Setup mock response
    mock_response = MagicMock()
    mock_response.body = {
        "hits": {
            "total": {"value": 2},
            "hits": [
                {
                    "_id": "1",
                    "_score": 1.0,
                    "_source": {
                        "bildnummer": "123456",
                        "datum": "2023-01-01",
                        "suchtext": "Test image 1",
                        "fotografen": "Test Photographer",
                        "hoehe": "1000",
                        "breite": "2000",
                        "db": "st",
                    },
                },
                {
                    "_id": "2",
                    "_score": 1.0,
                    "_source": {
                        "bildnummer": "789012",
                        "datum": "2023-01-02",
                        "suchtext": "Test image 2",
                        "fotografen": "Another Photographer",
                        "hoehe": "1200",
                        "breite": "1800",
                        "db": "sp",
                    },
                },
            ],
        }
    }
    mock_es_client.search.return_value = mock_response

    # Call the method
    result = es_service.search("", page=1, size=10)

    # Verify the result
    assert result["total"] == 2
    assert len(result["hits"]) == 2
    assert result["hits"][0]["id"] == "1"
    assert result["hits"][0]["bildnummer"] == "123456"
    assert result["hits"][1]["id"] == "2"
    assert result["hits"][1]["bildnummer"] == "789012"

    # Verify the correct query was sent
    mock_es_client.search.assert_called_once()
    args, kwargs = mock_es_client.search.call_args
    assert kwargs["index"] == "test-index"
    assert kwargs["query"] == {"match_all": {}}


def test_search_with_query(es_service, mock_es_client):
    """Test searching with a specific query"""
    # Setup mock response
    mock_response = MagicMock()
    mock_response.body = {
        "hits": {
            "total": {"value": 1},
            "hits": [
                {
                    "_id": "1",
                    "_score": 2.5,
                    "_source": {
                        "bildnummer": "123456",
                        "datum": "2023-01-01",
                        "suchtext": "Test image 1",
                        "fotografen": "Test Photographer",
                        "hoehe": "1000",
                        "breite": "2000",
                        "db": "st",
                    },
                }
            ],
        }
    }
    mock_es_client.search.return_value = mock_response

    # Call the method
    result = es_service.search("test query", page=1, size=10)

    # Verify the result
    assert result["total"] == 1
    assert len(result["hits"]) == 1
    assert result["hits"][0]["id"] == "1"
    assert result["hits"][0]["score"] == 2.5

    # Verify the correct query was sent
    mock_es_client.search.assert_called_once()
    args, kwargs = mock_es_client.search.call_args
    assert kwargs["index"] == "test-index"
    assert kwargs["query"]["multi_match"]["query"] == "test query"


def test_get_by_id_found(es_service, mock_es_client):
    """Test getting a media item by ID when it exists"""
    # Setup mock response
    mock_response = MagicMock()
    mock_response.body = {
        "hits": {
            "total": {"value": 1},
            "hits": [
                {
                    "_id": "1",
                    "_score": 1.0,
                    "_source": {
                        "bildnummer": "123456",
                        "datum": "2023-01-01",
                        "suchtext": "Test image 1",
                        "fotografen": "Test Photographer",
                        "hoehe": "1000",
                        "breite": "2000",
                        "db": "st",
                    },
                }
            ],
        }
    }
    mock_es_client.search.return_value = mock_response

    # Call the method
    result = es_service.get_by_id("123456")

    # Verify the result
    assert result is not None
    assert result["id"] == "1"
    assert result["bildnummer"] == "123456"

    # Verify the correct query was sent
    mock_es_client.search.assert_called_once()
    args, kwargs = mock_es_client.search.call_args
    assert kwargs["index"] == "test-index"
    assert kwargs["query"]["term"]["bildnummer"] == "123456"


def test_get_by_id_not_found(es_service, mock_es_client):
    """Test getting a media item by ID when it doesn't exist"""
    # Setup mock response with no hits
    mock_response = MagicMock()
    mock_response.body = {"hits": {"total": {"value": 0}, "hits": []}}
    mock_es_client.search.return_value = mock_response

    # Call the method
    result = es_service.get_by_id("nonexistent")

    # Verify the result
    assert result is None

    # Verify the correct query was sent
    mock_es_client.search.assert_called_once()


def test_filter_with_filters(es_service, mock_es_client):
    """Test filtering with specific criteria"""
    # Setup mock response
    mock_response = MagicMock()
    mock_response.body = {
        "hits": {
            "total": {"value": 1},
            "hits": [
                {
                    "_id": "1",
                    "_score": 1.0,
                    "_source": {
                        "bildnummer": "123456",
                        "datum": "2023-01-01",
                        "suchtext": "Test image 1",
                        "fotografen": "Test Photographer",
                        "hoehe": "1000",
                        "breite": "2000",
                        "db": "st",
                    },
                }
            ],
        }
    }
    mock_es_client.search.return_value = mock_response

    # Call the method with filters
    filters = {
        "photographer": "Test Photographer",
        "min_date": "2023-01-01",
        "max_date": "2023-01-31",
    }
    result = es_service.filter(filters, page=1, size=10)

    # Verify the result
    assert result["total"] == 1
    assert len(result["hits"]) == 1

    # Verify the correct query was sent
    mock_es_client.search.assert_called_once()
    args, kwargs = mock_es_client.search.call_args

    # Check that boolean query was used
    assert "bool" in kwargs["query"]
    assert "filter" in kwargs["query"]["bool"]

    # Get the filter conditions
    filter_conditions = kwargs["query"]["bool"]["filter"]

    # Check for photographer filter
    photographer_filter = None
    for condition in filter_conditions:
        if "term" in condition and "fotografen" in condition["term"]:
            photographer_filter = condition
            break
    assert photographer_filter is not None
    assert photographer_filter["term"]["fotografen"] == "Test Photographer"

    # Check for date range filters
    min_date_filter = None
    max_date_filter = None
    for condition in filter_conditions:
        if "range" in condition and "datum" in condition["range"]:
            if "gte" in condition["range"]["datum"]:
                min_date_filter = condition
            elif "lte" in condition["range"]["datum"]:
                max_date_filter = condition

    assert min_date_filter is not None
    assert min_date_filter["range"]["datum"]["gte"] == "2023-01-01"

    assert max_date_filter is not None
    assert max_date_filter["range"]["datum"]["lte"] == "2023-01-31"


def test_normalize_item():
    """Test the item normalization function"""
    # Create an ElasticsearchService instance directly
    with patch.object(ElasticsearchService, "__init__", return_value=None):
        service = ElasticsearchService(
            host="test-host",
            port=9200,
            index="test-index",
            username="test-user",
            password="test-pass",
            verify_certs=False,
        )

        # Also patch the client creation since we don't need it for this test
        service.client = MagicMock()

        # Test with a complete item
        complete_item = {
            "bildnummer": 12345,  # Integer should be converted to string
            "datum": "2023-01-01",
            "suchtext": "Test image",
            "fotografen": "Test Photographer",
            "hoehe": "1000",  # String should be converted to int
            "breite": "2000",
            "db": "st",
        }

        service._normalize_item(complete_item)

        assert complete_item["bildnummer"] == "12345"
        assert complete_item["hoehe"] == 1000
        assert complete_item["breite"] == 2000

        # Test with a partial item
        partial_item = {"bildnummer": "67890", "suchtext": "Partial test image"}

        service._normalize_item(partial_item)

        # Check defaults were applied
        assert partial_item["datum"] == ""
        assert partial_item["fotografen"] == ""
        assert partial_item["hoehe"] == 0
        assert partial_item["breite"] == 0
        assert partial_item["db"] == "st"
