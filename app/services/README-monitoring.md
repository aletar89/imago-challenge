# Prometheus Monitoring for API Endpoints

This application includes Prometheus monitoring for API endpoints. The monitoring collects metrics on:

- Request counts
- Error counts by type
- Execution time (latency)

## Metrics Endpoint

Metrics are exposed at the `/metrics` endpoint in Prometheus format, which can be scraped by a Prometheus server.

## API Monitoring Decorator

The main decorator provided for monitoring API endpoints:

### `@monitor_api(endpoint=None)`

Use this decorator on API route functions to monitor requests, errors, and execution time:

```python
from app.services.monitoring import monitor_api

@app.route("/example")
@monitor_api(endpoint="custom_name")  # Optional custom endpoint name
def example_route():
    # Function implementation
    return response
```

If no endpoint name is provided, the function name will be used as the endpoint name.

## Available Metrics

The following metrics are available at the `/metrics` endpoint:

- `api_requests_total` - Counter of total API requests (labeled by endpoint and HTTP method)
- `api_errors_total` - Counter of API errors (labeled by endpoint, HTTP method, and error type)
- `api_request_latency_seconds` - Histogram of API request latency (labeled by endpoint and HTTP method)

## Setting Up Prometheus

To monitor these metrics, you'll need to:

1. Install Prometheus from [prometheus.io](https://prometheus.io/)
2. Configure Prometheus to scrape the `/metrics` endpoint
3. Optionally set up Grafana for visualization

Example Prometheus configuration:

```yaml
scrape_configs:
  - job_name: 'flask-api'
    scrape_interval: 15s
    static_configs:
      - targets: ['localhost:5000']  # Adjust to your application's host:port
```

## Requirements

The monitoring functionality requires the `prometheus_client` package to be installed:

```
pip install prometheus_client
```

## Customizing Metrics

If you need to create custom metrics beyond what's provided by the decorator, import the required classes from prometheus_client:

```python
from prometheus_client import Counter, Gauge, Histogram, Summary

# Example custom counter
MY_COUNTER = Counter('my_counter_total', 'Description of counter', ['label1', 'label2'])

# Incrementing the counter
MY_COUNTER.labels(label1='value1', label2='value2').inc()
``` 