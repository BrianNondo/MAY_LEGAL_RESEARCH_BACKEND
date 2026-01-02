# config.py
import os
from dotenv import load_dotenv
from opensearchpy import OpenSearch, exceptions

# Load environment variables from .env file
load_dotenv()

# ---------- OPENSEARCH CONNECTION ----------
try:
    client = OpenSearch(
        hosts=[{
            'host': os.getenv('OPENSEARCH_HOST', 'localhost'),
            'port': int(os.getenv('OPENSEARCH_PORT', 9200))
        }],
        http_auth=(
            os.getenv('OPENSEARCH_USERNAME', 'admin'),
            os.getenv('OPENSEARCH_PASSWORD', 'admin')
        ),
        use_ssl=True,
        verify_certs=True,
        timeout=30
    )

    # Test connection
    if not client.ping():
        raise Exception("Cannot connect to OpenSearch")

    print(f"✅ Successfully connected to OpenSearch at {os.getenv('OPENSEARCH_HOST')}")

except Exception as e:
    print(f"❌ ERROR: Could not connect to OpenSearch: {e}")
    print("Please check your .env file configuration")
    client = None

# Get index name from environment
index_name = os.getenv('OPENSEARCH_INDEX', 'may_sme_legal_cases')