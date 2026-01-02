from config import client, index_name
from opensearchpy import exceptions

if client is None:
    print("❌ OpenSearch client not initialized")
    exit(1)

try:
    response = client.delete_by_query(
        index=index_name,
        body={
            "query": {
                "match_all": {}
            }
        },
        refresh=True,
        conflicts="proceed"
    )

    print("✅ All documents deleted successfully")
    print(f"Deleted documents count: {response.get('deleted', 0)}")

except exceptions.NotFoundError:
    print(f"⚠️ Index '{index_name}' does not exist")

except Exception as e:
    print(f"❌ Error deleting documents: {e}")
