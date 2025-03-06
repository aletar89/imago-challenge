# Imago Coding Challenge C3

A Flask application for retrieving and displaying media content from Elasticsearch.

Temprarily deployed on Render.com here: [https://imago-challenge.onrender.com](https://imago-challenge.onrender.com)

## Features

- **API Backend**: RESTful API endpoint for searching and filtering media content
- **Media Gallery**: Simple Bootstrap based frontend to browse, search, filter and view media
- **Easily expandable**: Additional media sources can be easily added by inheriting from an abstract `MediaFetchService` class
- **Data Normalization**: Handles missing fields and inconsistent data formats
- **Input Sanitization**: Handles potential malicious injections in user generated fields
- **Prometheus Monitoring**: API endpoint monitoring with metrics for request counts, errors, and latency
- **Integration tests**: Tests using the dev ES server to check the API is working end to end

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

### Testing

Run the tests using pytest:

```
python -m pytest -v
```


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



