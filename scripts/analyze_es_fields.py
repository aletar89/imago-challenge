#!/usr/bin/env python3
"""
Script to analyze field properties from a random sample of Elasticsearch entries.

This script fetches a random sample of 500 entries from Elasticsearch and analyzes:
- Field presence (which fields exist in documents)
- Field data types
- Field cardinality (number of unique values)
"""

from collections import defaultdict
import os
import sys
import logging
import argparse
import json
from typing import Any
from dotenv import load_dotenv

# Add the parent directory to the Python path to allow importing app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the ElasticsearchService class
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
    # Load environment variables
    env_vars = load_env_variables()

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

    # Validate that required index is provided in .env
    if not env_vars["index"]:
        parser.error("Index name is required. Set ELASTICSEARCH_INDEX in .env file.")

    return args, env_vars


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
    logging.info(f"Fetching random sample of {size} documents...")

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

    # Process the results
    results = es_service._process_search_results(response)

    logging.info(f"Retrieved {len(results['hits'])} documents")
    return results["hits"]


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
    report = {"total_documents": total_docs, "fields": {}}

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
    Process a document recursively to gather field information.

    Args:
        doc: Document dictionary
        prefix: Field name prefix for nested fields
        fields_presence: Dictionary to track field presence
        fields_types: Dictionary to track field types
        fields_values: Dictionary to track field values
    """
    for key, value in doc.items():
        field_name = f"{prefix}.{key}" if prefix else key

        # Count field presence
        fields_presence[field_name] += 1

        # Determine and count field type
        if value is None:
            type_name = "null"
        elif isinstance(value, dict):
            type_name = "object"
            # Recursively process nested object
            process_document(
                value, field_name, fields_presence, fields_types, fields_values
            )
        elif isinstance(value, list):
            type_name = "array"
            # Don't track values for arrays, but count presence
            # Process array elements if they're objects
            for i, item in enumerate(value):
                if isinstance(item, dict):
                    process_document(
                        item,
                        f"{field_name}[{i}]",
                        fields_presence,
                        fields_types,
                        fields_values,
                    )
        else:
            type_name = type(value).__name__
            # Add value for cardinality calculation (convert to string to ensure hashability)
            # Only track if not too large to prevent memory issues
            if not isinstance(value, (bytes, bytearray)) and (
                not isinstance(value, str) or len(value) < 1000
            ):
                try:
                    fields_values[field_name].add(str(value))
                except:
                    # Skip unhashable or problematic values
                    pass

        fields_types[field_name][type_name] += 1


def print_report(report: dict[str, Any]) -> None:
    """Print a human-readable summary of the report"""
    print(f"\nAnalysis of {report['total_documents']} documents:")
    print(f"Found {len(report['fields'])} distinct fields\n")

    print(
        "| {:<30} | {:^10} | {:<30} | {:>10} |".format(
            "Field", "Presence %", "Types", "Cardinality"
        )
    )
    print("|{:-<30}-|-{:-^10}-|-{:-<30}-|-{:->10}-|".format("", "", "", ""))

    for field, data in report["fields"].items():
        presence = f"{data['presence_percentage']}%"
        types = ", ".join(data["types"].keys())
        cardinality = data["cardinality"]

        print(f"| {field:<30} | {presence:^10} | {types:<30} | {cardinality:>10} |")


def main():
    """Main function"""
    setup_logging()
    args, env_vars = parse_args()

    try:
        # Initialize ElasticsearchService
        es_service = ElasticsearchService(
            host=env_vars["host"],
            port=env_vars["port"],
            index=env_vars["index"],
            username=env_vars["username"],
            password=env_vars["password"],
            verify_certs=False,
        )

        # Get random document sample
        documents = get_random_sample(es_service, args.sample_size)

        # Analyze field properties
        report = analyze_field_properties(documents)

        # Print report
        print_report(report)

        # Save report to file if requested
        if args.output:
            with open(args.output, "w") as f:
                json.dump(report, f, indent=2)
            logging.info(f"Report saved to {args.output}")

    except Exception as e:
        logging.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
