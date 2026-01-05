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
    All fields are included with star formatting for emphasis.
    """

    source = document.get("_source", {})
    lines = []

    # Title with stars
    title = source.get("title", "No Title")
    lines.append(f"\n***** {title} *****\n")

    # Metadata section header
    lines.append("*Metadata*")
    lines.append(f"*Index*: {document.get('_index')}")
    lines.append(f"*Document ID*: {document.get('_id')}")
    lines.append(f"*Score*: {document.get('_score')}")
    lines.append(f"*Document Type*: {source.get('document_type', 'N/A')}")
    lines.append(f"*Court*: {source.get('court_type', 'N/A')}")
    lines.append(f"*Case Category*: {source.get('case_category', 'N/A')}")
    lines.append(f"*Case Status*: {source.get('case_status', 'N/A')}")
    lines.append(f"*Subject*: {source.get('subject', 'N/A')}")
    lines.append(f"*Result*: {source.get('result', 'N/A')}")
    lines.append(f"*Plaintiff Wins*: {source.get('plaintiff_wins', 'N/A')}")
    lines.append(f"*Defendant Wins*: {source.get('defendant_wins', 'N/A')}")
    lines.append(f"*Case Outcome*: {source.get('case_outcome', 'N/A')}")
    lines.append(f"*Outcome Reason*: {source.get('outcome_reason', 'N/A')}")
    lines.append(f"*Outcome Summary*: {source.get('outcome_summary', 'N/A')}")
    lines.append(f"*Evidence by Plaintiff*: {source.get('evidence_by_plaintiff', 'N/A')}")
    lines.append(f"*Evidence by Defendant*: {source.get('evidence_by_defendant', 'N/A')}")

    # People
    people = source.get("people", [])
    if people:
        lines.append("\n*People Involved*:")
        for p in people:
            name = p.get('name', 'N/A')
            role = p.get('role', 'N/A')
            identity_type = p.get('identity_type', 'N/A')
            lines.append(f" - *Name*: {name}, *Role*: {role}, *Type*: {identity_type}")

    # Keywords
    keywords = source.get("keywords", [])
    if keywords:
        lines.append("\n*Keywords*:")
        for k in keywords:
            lines.append(f" - {k}")

    # Key points
    points = source.get("points_simple", [])
    if points:
        lines.append("\n*Key Points*:")
        for i, point in enumerate(points, 1):
            lines.append(f" {i}. {point}")

    # Files
    source_url = source.get("source_url", "N/A")
    lines.append("\n*Files*:")
    lines.append(f" - *Source URL*: {source_url}")

    # Full text
    full_text = source.get("full_text", "")
    if full_text:
        # Format important parts of full text with stars
        formatted_full_text = format_full_text_with_stars(full_text)
        lines.append("\n*Full Text*:\n" + formatted_full_text)

    return "\n".join(lines)


def format_full_text_with_stars(text: str) -> str:
    """
    Adds star formatting to important parts of the full text.
    """
    # This is a simple formatter - you can enhance it based on your needs
    formatted = text

    # Format common legal terms with stars
    legal_terms = [
        ("court", "*Court*:"),
        ("judge", "*Judge*:"),
        ("plaintiff", "*Plaintiff*:"),
        ("defendant", "*Defendant*:"),
        ("witness", "*Witness*:"),
        ("evidence", "*Evidence*:"),
        ("verdict", "*Verdict*:"),
        ("sentence", "*Sentence*:"),
        ("appeal", "*Appeal*:"),
        ("statute", "*Statute*:"),
        ("regulation", "*Regulation*:"),
    ]

    for term, replacement in legal_terms:
        # Case insensitive replacement for whole words
        import re
        formatted = re.sub(rf'\b{term}\b', replacement, formatted, flags=re.IGNORECASE)

    return formatted