"""
Monitoring module for the application.

This module provides decorators for monitoring API endpoints and services
using Prometheus metrics.
"""

import functools
import time
from typing import Any, Callable, TypeVar, cast

from flask import request
from prometheus_client import Counter, Histogram

# Type variable for the decorator's function
F = TypeVar("F", bound=Callable[..., Any])

# Prometheus metrics
API_REQUESTS = Counter(
    "api_requests_total", "Total count of API requests", ["endpoint", "method"]
)

API_ERRORS = Counter(
    "api_errors_total",
    "Total count of API errors",
    ["endpoint", "method", "error_type"],
)

API_LATENCY = Histogram(
    "api_request_latency_seconds",
    "API request latency in seconds",
    ["endpoint", "method"],
    buckets=(
        0.01,
        0.025,
        0.05,
        0.075,
        0.1,
        0.25,
        0.5,
        0.75,
        1.0,
        2.5,
        5.0,
        7.5,
        10.0,
        float("inf"),
    ),
)


def monitor_api(endpoint: str | None = None) -> Callable[[F], F]:
    """
    Decorator for monitoring API endpoints with Prometheus metrics.

    Args:
        endpoint: Name of the endpoint being monitored. If None, it will
                 be inferred from the function name.

    Returns:
        Decorator function
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            nonlocal endpoint

            # If endpoint name not provided, use function name
            if endpoint is None:
                endpoint_name = func.__name__
            else:
                endpoint_name = endpoint

            # Try to get it from request context if available
            method = "unknown"
            try:
                method = request.method
            except RuntimeError:
                pass

            # Increment request counter
            API_REQUESTS.labels(endpoint=endpoint_name, method=method).inc()

            # Measure execution time
            start_time = time.time()

            try:
                result = func(*args, **kwargs)
                # Record latency
                API_LATENCY.labels(endpoint=endpoint_name, method=method).observe(
                    time.time() - start_time
                )
                return result
            except Exception as e:
                # Record error and latency
                API_ERRORS.labels(
                    endpoint=endpoint_name,
                    method=method,
                    error_type=e.__class__.__name__,
                ).inc()
                API_LATENCY.labels(endpoint=endpoint_name, method=method).observe(
                    time.time() - start_time
                )
                raise

        return cast(F, wrapper)

    return decorator
