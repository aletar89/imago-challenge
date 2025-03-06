# Elasticsearch Analysis Scripts

This directory contains scripts for analyzing and working with Elasticsearch data.

## analyze_es_fields.py

This script analyzes field properties from a random sample of Elasticsearch documents. It helps you understand:

- Field presence (percentage of documents containing each field)
- Field data types (what types each field contains)
- Field cardinality (number of unique values for each field)

### Configuration

The script can read Elasticsearch configuration from:

1. Environment variables in the `.env` file:
   ```
   ELASTICSEARCH_HOST=https://elasticsearch.example.com
   ELASTICSEARCH_PORT=9200
   ELASTICSEARCH_INDEX=media_archive
   ELASTICSEARCH_USER=elastic
   ELASTICSEARCH_PASSWORD=your_password
   ```

2. Command line arguments (which override values from the `.env` file)

### Usage

```bash
# Basic usage (reads configuration from .env file)
python scripts/analyze_es_fields.py

# Override specific settings from command line
python scripts/analyze_es_fields.py --index custom_index --sample-size 1000
```

### Required Parameters

- Elasticsearch index name (from `.env` file or `--index` parameter)

### Optional Parameters

- `--host HOST`: Elasticsearch host (default: from .env or localhost)
- `--port PORT`: Elasticsearch port (default: from .env or 9200)
- `--username USERNAME`: Elasticsearch username (default: from .env)
- `--password PASSWORD`: Elasticsearch password (default: from .env)
- `--no-verify-certs`: Disable SSL certificate verification (default behavior)
- `--verify-certs`: Enable SSL certificate verification
- `--sample-size SAMPLE_SIZE`: Number of random documents to sample (default: 500)
- `--output OUTPUT`: Path to save the JSON report (optional)

### SSL Certificate Verification

When using the script with Elasticsearch over HTTPS:

- By default, SSL certificate verification is **disabled** when using configuration from `.env` file
- Use `--verify-certs` to explicitly enable certificate verification
- Use `--no-verify-certs` to explicitly disable certificate verification

### Examples

```bash
# Basic usage - reads credentials and index from .env
python scripts/analyze_es_fields.py

# Enable SSL certificate verification
python scripts/analyze_es_fields.py --verify-certs

# Override specific settings
python scripts/analyze_es_fields.py --host elasticsearch.example.com --index test_index

# Analyze a larger sample and save the report to a file
python scripts/analyze_es_fields.py --sample-size 1000 --output field_analysis.json
```

### Output Format

The script outputs a table showing:

- Field name
- Presence percentage (how often the field appears)
- Data types found in the field
- Cardinality (number of unique values)

If you specify an output file, a detailed JSON report will be saved with all analysis data.

### Example Output

```
Analysis of 500 documents:
Found 25 distinct fields

| Field        | Presence % | Types        | Cardinality |
|--------------|------------|--------------|-------------|
| bildnummer   | 100.0%     | str, int     | 500         |
| suchtext     | 98.2%      | str          | 489         |
| datum        | 95.6%      | str          | 231         |
| fotografen   | 93.8%      | str          | 47          |
| hoehe        | 89.4%      | int, str     | 87          |
| breite       | 89.4%      | int, str     | 112         |
| db           | 100.0%     | str          | 1           |
``` 