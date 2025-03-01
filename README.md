# Imago Media API and Gallery

A Flask application for retrieving and displaying media content from Elasticsearch.

## Features

- **API Backend**: RESTful API endpoints for searching and filtering media content
- **Media Gallery**: User-friendly frontend to browse, search, and view media
- **Robust Search**: Keyword-based search and filtering with pagination
- **Data Normalization**: Handles missing fields and inconsistent data formats

## Getting Started

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Installation

1. Clone the repository
2. Create a virtual environment and activate it:
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
   - Edit `.env` with your Elasticsearch credentials and other configuration values

### Running the Application

1. Start the Flask development server:
   ```
   python app.py
   ```
2. Open your browser and navigate to `http://localhost:5000`

## Environment Variables

The application uses the following environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| ELASTICSEARCH_HOST | Elasticsearch host URL | http://localhost |
| ELASTICSEARCH_PORT | Elasticsearch port number | 9200 |
| ELASTICSEARCH_INDEX | Index name for media data | media |
| ELASTICSEARCH_USER | Username for Elasticsearch | (empty) |
| ELASTICSEARCH_PASSWORD | Password for Elasticsearch | (empty) |
| IMAGE_BASE_URL | Base URL for image paths | https://example.com |

## API Endpoints

### Search Media

```
GET /api/search
```

Query parameters:
- `q`: Search query string
- `page`: Page number (default: 1)
- `size`: Number of results per page (default: 10)

### Get Media by ID

```
GET /api/media/<media_id>
```

### Filter Media

```
GET /api/filter
```

Query parameters:
- `photographer`: Filter by photographer name
- `min_date`: Filter by minimum date
- `max_date`: Filter by maximum date
- `page`: Page number (default: 1)
- `size`: Number of results per page (default: 10)

## Data Normalization

The application normalizes media data to ensure consistency:

- Missing fields are populated with sensible defaults
- Data types are converted as needed (strings to numbers, etc.)
- Media IDs are padded to 10 characters for constructing image URLs

## Testing

Run the tests using pytest:

```
python -m pytest -v
```

## Project Structure

```
├── app/
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── services/
│   │   ├── __init__.py
│   │   └── elasticsearch_service.py
│   ├── templates/
│   │   └── index.html
│   ├── __init__.py
│   └── routes.py
├── tests/
│   ├── test_api_routes.py
│   └── test_elasticsearch_service.py
├── app.py
├── .env.example
├── requirements.txt
└── README.md
```

## Design Decisions

- **Flask**: Lightweight web framework that's easy to set up and use
- **Service Layer**: Abstraction over Elasticsearch for better testability
- **REST API**: Provides a clean interface for accessing media data
- **Client-Side Rendering**: JavaScript-based frontend for responsive user experience
- **Bootstrap**: Modern, responsive UI components