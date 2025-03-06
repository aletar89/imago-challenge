# Imago Media API and Gallery

A Flask application for retrieving and displaying media content from Elasticsearch.

## Features

- **API Backend**: RESTful API endpoint for searching and filtering media content
- **Media Gallery**: User-friendly frontend to browse, search, filter and view media
- **Robust Search**: Keyword-based search and filtering with pagination
- **Data Normalization**: Handles missing fields and inconsistent data formats
- **Prometheus Monitoring**: API endpoint monitoring with metrics for request counts, errors, and latency

## Design Decisions

- **Flask**: Lightweight web framework that's easy to set up and use
- **Service Layer**: Abstraction over Elasticsearch using the MediaFetchService interface for better testability and flexibility
- **REST API**: Provides a clean interface for accessing media data with comprehensive filtering options
- **Client-Side Rendering**: JavaScript-based frontend for responsive user experience
- **Bootstrap**: Modern, responsive UI components
- **Prometheus Monitoring**: Industry-standard monitoring solution for tracking API performance and reliability
- **Data Normalization**: Careful handling of data inconsistencies and security concerns through sanitization
- **Abstract Base Classes**: Use of ABC for service interfaces to ensure consistent implementation
- **Environment Configuration**: Configuration via environment variables for better security and deployment flexibility

## Getting Started


### Installation

1. Clone the repository
2. (Optional) Create a virtual environment and activate it:
   ```
   python -m venv venv
   venv\Scripts\activate  # Windows
   source venv/bin/activate  # Unix/Mac
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Configure environment variables:
   - Copy `.env.example` to `.env`
   - Edit `.env` with your Elasticsearch credentials

### Running the Application

1. Start the Flask development server:
   ```
   python app.py
   ```
2. Open your browser and navigate to `http://localhost:5000`


## API Endpoints

### Search Media

```
GET /api/search
```

Query parameters:
- `q`: Search query string
- `page`: Page number (default: 1)
- `size`: Number of results per page (default: 10)

Filter parameters:
- Currently implemented in front-end:
  - `photographer`: Filter by photographer name
  - `min_date`/`max_date`: Filter by date range

Response format:
```json
{
  "total": 42,
  "hits": [
    {
      "id": "media123",
      "title": "Example Media Title",
      "description": "Detailed description of the media item",
      "photographer": "Photographer Name",
      "date": "2023-04-15",
      "thumbnail_url": "https://example.com/thumbnail.jpg",
      "additional_data": {
        "score": 0.95,
        "bildnummer": "1234567890",
        "db": "st",
        "hoehe": 300,
        "breite": 400
      }
    }
  ]
}
```


## Data Normalization

The application normalizes media data to ensure consistency and security:

- Data types are converted as needed (strings to numbers, etc.)
- Media IDs (bildnummer) are padded to 10 characters for constructing image URLs
- String values are sanitized to remove HTML tags for security
- Sanitized strings are limited to a reasonable maximum length (500 characters)
- Default values are provided for missing required fields
- Thumbnails are generated with consistent URL patterns
- Title and description fields are derived from available data:
  - If title is not available, a truncated version of the search text is used
  - If description is not available, the full search text is used
- Relevance scores are stored in the additional_data field

## Monitoring

The application includes Prometheus monitoring for API endpoints, collecting metrics on:

- Request counts (by endpoint and HTTP method)
- Error counts (by endpoint, HTTP method, and error type)
- Execution time/latency (by endpoint and HTTP method)

To use this feature, ensure the `prometheus_client` package is installed. Metrics are exposed at the `/metrics` endpoint in Prometheus format.

## Testing

Run the tests using pytest:

```
python -m pytest -v
```


