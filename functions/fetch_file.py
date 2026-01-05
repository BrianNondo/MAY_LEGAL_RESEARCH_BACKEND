# functions/get_document.py

from config import client, index_name


def fetch_file(text: str) -> str:
    """
    Detects `get_file:` command and returns a full readable message.
    No JSON, formatted with stars for the title and all fields included.
    """

    if "get_file:" not in text:
        return None

    document_id = text.split("get_file:", 1)[1].strip()

    if not document_id:
        return "❌ get_file command detected, but no document ID was provided."

    document = get_document_by_id(document_id)

    if not document:
        return f"❌ No document found with ID: {document_id}"

    return format_document_message(document)


def get_document_by_id(document_id: str):
    """
    Retrieves a document using OpenSearch _id (authoritative ID).
    """

    try:
        response = client.get(
            index=index_name,
            id=document_id
        )
        return response

    except Exception as e:
        print(f"[OpenSearch ERROR] {e}")
        return None


def format_document_message(document: dict) -> str:
    """
    Formats the OpenSearch document as a readable message.
    All fields are included. Title surrounded by stars.
    """

    source = document.get("_source", {})
    lines = []

    # Title
    title = source.get("title", "No Title")
    lines.append(f"\n***** {title} *****\n")

    # Metadata
    lines.append(f"Index: {document.get('_index')}")
    lines.append(f"Document ID: {document.get('_id')}")
    lines.append(f"Score: {document.get('_score')}")
    lines.append(f"Document Type: {source.get('document_type', 'N/A')}")
    lines.append(f"Court: {source.get('court_type', 'N/A')}")
    lines.append(f"Case Category: {source.get('case_category', 'N/A')}")
    lines.append(f"Case Status: {source.get('case_status', 'N/A')}")
    lines.append(f"Subject: {source.get('subject', 'N/A')}")
    lines.append(f"Result: {source.get('result', 'N/A')}")
    lines.append(f"Plaintiff Wins: {source.get('plaintiff_wins', 'N/A')}")
    lines.append(f"Defendant Wins: {source.get('defendant_wins', 'N/A')}")
    lines.append(f"Case Outcome: {source.get('case_outcome', 'N/A')}")
    lines.append(f"Outcome Reason: {source.get('outcome_reason', 'N/A')}")
    lines.append(f"Outcome Summary: {source.get('outcome_summary', 'N/A')}")
    lines.append(f"Evidence by Plaintiff: {source.get('evidence_by_plaintiff', 'N/A')}")
    lines.append(f"Evidence by Defendant: {source.get('evidence_by_defendant', 'N/A')}")

    # People
    people = source.get("people", [])
    if people:
        lines.append("\nPeople Involved:")
        for p in people:
            lines.append(f" - Name: {p.get('name', 'N/A')}, Role: {p.get('role', 'N/A')}, Type: {p.get('identity_type', 'N/A')}")

    # Entities
    entities = source.get("entities", [])
    if entities:
        lines.append("\nEntities:")
        for e in entities:
            lines.append(f" - {e}")

    # Keywords
    keywords = source.get("keywords", [])
    if keywords:
        lines.append("\nKeywords:")
        for k in keywords:
            lines.append(f" - {k}")

    # Key points
    points = source.get("points_simple", [])
    if points:
        lines.append("\nKey Points:")
        for i, point in enumerate(points, 1):
            lines.append(f" {i}. {point}")

    # Files
    lines.append("\nFiles:")
    lines.append(f" - JSON File: {source.get('json_filename', 'N/A')}")
    lines.append(f" - TXT File: {source.get('txt_filename', 'N/A')}")
    lines.append(f" - Source URL: {source.get('source_url', 'N/A')}")

    # Full text
    full_text = source.get("full_text", "")
    if full_text:
        lines.append("\nFull Text:\n" + full_text)

    return "\n".join(lines)
