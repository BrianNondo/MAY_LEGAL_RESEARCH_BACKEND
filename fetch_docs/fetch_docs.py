# fetch_documents.py
from config import client, index_name

if client is None:
    print("OpenSearch client is not connected.")
    exit()

try:
    # Query to get all documents
    response = client.search(
        index=index_name,
        body={
            "size": 1000,  # adjust if you have more documents
            "query": {
                "match_all": {}
            }
        }
    )

    documents = response['hits']['hits']
    print(f"Found {len(documents)} documents.\n")

    # Print the source_url for each document
    for doc in documents:
        source_url = doc['_source'].get('source_url', None)
        if source_url:
            print(source_url)

except Exception as e:
    print(f"Error fetching documents: {e}")
