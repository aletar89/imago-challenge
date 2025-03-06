#!/usr/bin/env python3
"""
Script to analyze field properties from a random sample of Elasticsearch entries.

This script fetches a random sample of 500 entries from Elasticsearch and analyzes:
- Field presence (which fields exist in documents)
- Field data types
- Field cardinality (number of unique values)
"""

import argparse
import json
import logging
import os
import sys
from collections import defaultdict
from typing import Any

from dotenv import load_dotenv

from app.services.elasticsearch_service import ElasticsearchService


def setup_logging():
    """Configure logging"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def load_env_variables():
    """Load environment variables from .env file"""
    # Load environment variables from .env file
    dotenv_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"
    )
    load_dotenv(dotenv_path)

    return {
        "host": os.getenv("ELASTICSEARCH_HOST", "localhost"),
        "port": int(os.getenv("ELASTICSEARCH_PORT", "9200")),
        "index": os.getenv("ELASTICSEARCH_INDEX", ""),
        "username": os.getenv("ELASTICSEARCH_USER", ""),
        "password": os.getenv("ELASTICSEARCH_PASSWORD", ""),
    }


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Analyze field properties from Elasticsearch sample data"
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=500,
        help="Number of random documents to sample",
    )
    parser.add_argument("--output", help="Output file for the JSON report (optional)")

    args = parser.parse_args()
    return args


def get_random_sample(
    es_service: ElasticsearchService, size: int
) -> list[dict[str, Any]]:
    """
    Fetch a random sample of documents from Elasticsearch.

    Args:
        es_service: ElasticsearchService instance
        size: Number of documents to sample

    Returns:
        List of document dictionaries
    """
    logging.info("Fetching random sample of %d documents...", size)

    # Create a function_score query with random_score to get random documents
    random_query = {
        "function_score": {
            "query": {"match_all": {}},
            "random_score": {},
            "boost_mode": "replace",
        }
    }

    # Execute the search directly with the client
    response = es_service.client.search(
        index=es_service.index,
        query=random_query,
        size=size,
    )

    # Process the results - this returns a tuple (total_count, list of MediaItems)
    _, media_items = es_service.process_search_results(response)

    # Convert MediaItem objects to dictionaries
    documents = [item.to_dict() for item in media_items]

    logging.info("Retrieved %d documents", len(documents))
    return documents


def analyze_field_properties(documents: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Analyze field properties from a collection of documents.

    Args:
        documents: List of document dictionaries

    Returns:
        Dictionary with analysis results
    """
    logging.info("Analyzing field properties...")

    total_docs = len(documents)
    fields_presence: dict[str, int] = defaultdict(int)
    fields_types: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    fields_values: dict[str, set] = defaultdict(set)

    # Analyze each document
    for doc in documents:
        # Recursively process fields
        process_document(doc, "", fields_presence, fields_types, fields_values)

    # Calculate cardinality (number of unique values)
    fields_cardinality = {field: len(values) for field, values in fields_values.items()}

    # Calculate presence percentage
    fields_presence_pct = {
        field: (count / total_docs) * 100 for field, count in fields_presence.items()
    }

    # Sort fields by presence (descending)
    sorted_fields = sorted(
        fields_presence.keys(), key=lambda x: fields_presence[x], reverse=True
    )

    # Create final report
    report: dict[str, Any] = {"total_documents": total_docs, "fields": {}}

    for field in sorted_fields:
        report["fields"][field] = {
            "presence_count": fields_presence[field],
            "presence_percentage": round(fields_presence_pct[field], 2),
            "types": dict(fields_types[field]),
            "cardinality": fields_cardinality.get(field, 0),
        }

    return report


def process_document(
    doc: dict[str, Any],
    prefix: str,
    fields_presence: dict[str, int],
    fields_types: dict[str, dict[str, int]],
    fields_values: dict[str, set],
) -> None:
    """
    Process a document to extract field information

    Args:
        doc: Document to process
        prefix: Current field prefix (for nested fields)
        fields_presence: Dictionary to track field presence
        fields_types: Dictionary to track field types
        fields_values: Dictionary to track unique field values
    """
    for key, value in doc.items():
        field_name = f"{prefix}{key}" if prefix else key
        fields_presence[field_name] += 1

        # Determine the type
        type_name = type(value).__name__

        # For nested objects, recurse
        if isinstance(value, dict):
            process_document(
                value, f"{field_name}.", fields_presence, fields_types, fields_values
            )
        # For arrays, process each element
        elif (
            isinstance(value, list)
            and value
            and not isinstance(value[0], (int, float, str, bool))
        ):
            for item in value:
                if isinstance(item, dict):
                    process_document(
                        item,
                        f"{field_name}[].",
                        fields_presence,
                        fields_types,
                        fields_values,
                    )
        # For simple values, add to the set of unique values if it's a simple type
        elif isinstance(value, (int, float, str, bool)):
            try:
                fields_values[field_name].add(str(value))
            except TypeError:
                # Skip unhashable or problematic values
                pass

        fields_types[field_name][type_name] += 1


def print_report(report: dict[str, Any]) -> None:
    """Print a human-readable summary of the report"""
    print(f"\nAnalysis of {report['total_documents']} documents:")
    print(f"Found {len(report['fields'])} distinct fields\n")

    print(
        f"| {'Field':<30} | {'Presence %':^10} | {'Types':<30} | {'Cardinality':>10} |"
    )
    print(f"|{'-'*30}-|{'-'*10}-|{'-'*30}-|{'-'*10}-|")

    for field, data in report["fields"].items():
        # Truncate type information if needed
        type_str = str(data["types"])
        if len(type_str) > 30:
            type_str = type_str[:27] + "..."

        print(
            f"| {field:<30} | {data['presence_percentage']:^10.2f} | {type_str:<30} | {data['cardinality']:>10} |"
        )


def main():
    """Main function"""
    setup_logging()
    load_env_variables()
    args = parse_args()

    try:
        # Connect to Elasticsearch
        es_host = os.getenv("ES_HOST", "localhost")
        es_port = int(os.getenv("ES_PORT", "9200"))
        es_index = os.getenv("ES_INDEX", "imago")
        es_username = os.getenv("ES_USERNAME", "")
        es_password = os.getenv("ES_PASSWORD", "")

        # Initialize Elasticsearch service
        es_service = ElasticsearchService(
            host=es_host,
            port=es_port,
            index=es_index,
            username=es_username,
            password=es_password,
        )

        # Fetch random sample of documents
        documents = get_random_sample(es_service, args.sample_size)

        # Analyze field properties
        report = analyze_field_properties(documents)

        # Print report
        print_report(report)

        # Save report to file if requested
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2)
            logging.info("Report saved to %s", args.output)

    except (ValueError, ConnectionError, IOError) as e:
        logging.error("Error: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
