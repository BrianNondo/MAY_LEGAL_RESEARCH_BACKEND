# topics_functions.py
import random
from rapidfuzz import process
from opensearchpy import exceptions
from config import client, index_name
from collections import defaultdict

# Random AI-style responses for different scenarios
AI_RESPONSES = {
    "found_topics": [
        "I've analyzed the legal database and found the following relevant cases:",
        "After searching through the case records, here are the most relevant findings:",
        "Based on my analysis of legal documents, here are the cases matching your query:",
        "I've reviewed the case files and found these relevant matters:",
        "Here are the legal cases I found related to your area of interest:"
    ],
    "no_results": [
        "I couldn't find any cases specifically addressing that subject in the database.",
        "No matching cases were found for that particular legal subject.",
        "After searching the case records, I didn't find any cases related to that subject.",
        "The database doesn't contain any cases matching that specific query."
    ],
    "single_result": [
        "I found one relevant case in the legal records:",
        "There's one case that addresses this legal subject:",
        "One case was found related to your query:"
    ],
    "multiple_results": [
        "I found several cases that might be relevant to your inquiry:",
        "There are multiple case areas addressing this legal subject:",
        "Several cases in the database relate to this subject:"
    ]
}


# ---------- Helper function to separate comma-separated values ----------
def separate_comma_values(text):
    """Separate comma-separated values in text and return as list"""
    if not text:
        return []
    items = [item.strip() for item in text.split(',')]
    return [item for item in items if item]


# ---------- Updated search_topics ----------
def search_topics(topic, top_n=5):
    """Search OpenSearch for a topic and return relevant information"""
    search_body = {
        "query": {
            "bool": {
                "should": [
                    {"match": {"title": topic}},
                    {"match": {"keywords": topic}},
                    {"match": {"entities": topic}},
                    {"match": {"points_simple": topic}},
                    {"match": {"full_text": topic}},
                    {"match": {"document_type": topic}},
                    {"match": {"court_type": topic}},
                    {"match": {"case_category": topic}},
                    {"match": {"subject": topic}}
                ]
            }
        },
        "size": top_n,
        "aggs": {
            "document_types": {
                "terms": {
                    "field": "document_type.keyword",
                    "size": 10
                }
            },
            "court_types": {
                "terms": {
                    "field": "court_type.keyword",
                    "size": 10
                }
            }
        }
    }

    try:
        response = client.search(index=index_name, body=search_body)
        hits = response['hits']['hits']
        total_hits = response['hits']['total']['value']

        # Get aggregations
        doc_type_counts = response.get('aggregations', {}).get('document_types', {}).get('buckets', [])
        court_type_counts = response.get('aggregations', {}).get('court_types', {}).get('buckets', [])

        if not hits:
            return random.choice(AI_RESPONSES["no_results"])

        if total_hits == 1:
            intro = random.choice(AI_RESPONSES["single_result"])
        elif total_hits > 1:
            intro = random.choice(AI_RESPONSES["multiple_results"])
        else:
            intro = random.choice(AI_RESPONSES["found_topics"])

        message = f"{intro}\n\n"
        message += f"**Total Results:** {total_hits} case{'s' if total_hits != 1 else ''} related to '{topic}'\n\n"

        # Add document type statistics
        if doc_type_counts:
            message += "**Document Types Breakdown:**\n"
            for bucket in doc_type_counts:
                doc_type = bucket['key']
                count = bucket['doc_count']
                message += f"  • {doc_type}: {count} case{'s' if count != 1 else ''}\n"
            message += "\n"

        # Add court type statistics
        if court_type_counts:
            message += "**Court Types Breakdown:**\n"
            for bucket in court_type_counts:
                court_type = bucket['key']
                count = bucket['doc_count']
                message += f"  • {court_type}: {count} case{'s' if count != 1 else ''}\n"
            message += "\n"

        display_count = min(top_n, len(hits))
        for i, hit in enumerate(hits[:display_count], 1):
            src = hit['_source']
            doc_id = hit.get('_id', hit.get('document_id', 'N/A'))
            # Use actual case fields from the document format
            document_type = src.get('document_type', 'Not specified')
            court_type = src.get('court_type', 'Not specified')
            case_category = src.get('case_category', 'Not specified')

            message += f"**Case {i}. {src.get('title', 'Untitled Case')}**\n"
            message += f"**Document Type:** {document_type}\n"
            message += f"**Court:** {court_type}\n"
            message += f"**Category:** {case_category}\n"

            # Add people involved
            if src.get("people"):
                message += "**People Involved:**\n"
                for p in src['people']:
                    name = p.get('name', 'Unknown')
                    role = p.get('role', 'Unknown role')
                    message += f"  • {name} ({role})\n"

            # Add relevant points from points_simple
            if src.get("points_simple"):
                message += f"\n**Relevant Case Points:**\n"
                found_points = 0
                for pt in src['points_simple']:
                    # Check if topic appears in this point
                    if topic.lower() in pt.lower():
                        message += f"  • {pt}\n"
                        found_points += 1

                if found_points == 0:
                    # Show first few points if none specifically mention the topic
                    message += f"  • First point: {src['points_simple'][0][:150]}...\n"
                    if len(src['points_simple']) > 1:
                        message += f"  • Second point: {src['points_simple'][1][:150]}...\n"
                else:
                    message += f"\n  *{found_points} point{'s' if found_points != 1 else ''} specifically mention '{topic}'*\n"

            # Add outcome information
            if src.get("outcome_summary"):
                message += f"\n**Outcome Summary:** {src['outcome_summary']}\n"

            if src.get("case_outcome"):
                message += f"**Case Outcome:** {src['case_outcome']}\n"

            if src.get("result"):
                result = src['result']
                if result == "partial_success":
                    message += f"**Result:** Partial Success\n"
                elif result == "failure":
                    message += f"**Result:** Case Failed\n"
                elif result == "success":
                    message += f"**Result:** Case Succeeded\n"
                else:
                    message += f"**Result:** {result}\n"

            # Add case status if available
            if src.get("case_status"):
                status = src['case_status']
                status_map = {
                    "pending": "Pending",
                    "decided": "Decided",
                    "appealed": "Appealed",
                    "dismissed": "Dismissed"
                }
                message += f"**Status:** {status_map.get(status, status)}\n\n\n"
            message += f'<a href="#" class="see-more-link" data-docid="{doc_id}" style="color:#346969; text-decoration: underline;">See all ...</a><br>'
            message += "\n\n\n" + "=" * 60 + "\n\n"

        return message

    except exceptions.ConnectionError:
        return random.choice([
            "I'm having trouble connecting to the legal database at the moment.",
            "There seems to be a connection issue with the case records system.",
            "I can't access the legal database due to connectivity problems."
        ])
    except Exception as e:
        return f"{random.choice([
            'An unexpected error occurred while searching the legal database.',
            'I encountered an issue while processing your legal research request.',
            'There was a problem retrieving the case information you requested.'
        ])} Error details: {str(e)}"


# ---------- Specialized search functions ----------
def search_by_document_type(doc_type, top_n=5):
    """Search for cases by document type"""
    search_body = {
        "query": {
            "match": {
                "document_type": doc_type
            }
        },
        "size": top_n,
        "aggs": {
            "court_types_for_doc": {
                "terms": {
                    "field": "court_type.keyword",
                    "size": 10
                }
            },
            "categories_for_doc": {
                "terms": {
                    "field": "case_category.keyword",
                    "size": 10
                }
            }
        }
    }

    try:
        response = client.search(index=index_name, body=search_body)
        hits = response['hits']['hits']
        total_hits = response['hits']['total']['value']

        court_aggregations = response.get('aggregations', {}).get('court_types_for_doc', {}).get('buckets', [])

        if not hits:
            return f"No cases found with document type: '{doc_type}'"

        message = f"**Search Results for Document Type: {doc_type}**\n\n"
        message += f"**Total Cases:** {total_hits} case{'s' if total_hits != 1 else ''}\n\n"

        # Show court type distribution
        if court_aggregations:
            message += "**Court Distribution:**\n"
            for bucket in court_aggregations:
                court = bucket['key']
                count = bucket['doc_count']
                message += f"  • {court}: {count} case{'s' if count != 1 else ''}\n"
            message += "\n"

        # Show top cases
        display_count = min(top_n, len(hits))
        for i, hit in enumerate(hits[:display_count], 1):
            src = hit['_source']
            message += f"{i}. **{src.get('title', 'Untitled Case')}**\n"
            message += f"   Court: {src.get('court_type', 'N/A')}\n"
            message += f"   Category: {src.get('case_category', 'N/A')}\n"

            if src.get("outcome_summary"):
                summary = src['outcome_summary']
                if len(summary) > 150:
                    summary = summary[:150] + "..."
                message += f"   Outcome: {summary}\n"

            message += "\n"

        return message

    except Exception as e:
        return f"Error searching by document type: {str(e)}"


def search_by_court_type(court_type, top_n=5):
    """Search for cases by court type"""
    search_body = {
        "query": {
            "match": {
                "court_type": court_type
            }
        },
        "size": top_n,
        "aggs": {
            "doc_types_for_court": {
                "terms": {
                    "field": "document_type.keyword",
                    "size": 10
                }
            },
            "categories_for_court": {
                "terms": {
                    "field": "case_category.keyword",
                    "size": 10
                }
            }
        }
    }

    try:
        response = client.search(index=index_name, body=search_body)
        hits = response['hits']['hits']
        total_hits = response['hits']['total']['value']

        doc_aggregations = response.get('aggregations', {}).get('doc_types_for_court', {}).get('buckets', [])

        if not hits:
            return f"No cases found in court: '{court_type}'"

        message = f"**Search Results for Court: {court_type}**\n\n"
        message += f"**Total Cases:** {total_hits} case{'s' if total_hits != 1 else ''}\n\n"

        # Show document type distribution
        if doc_aggregations:
            message += "**Document Type Distribution:**\n"
            for bucket in doc_aggregations:
                doc_type = bucket['key']
                count = bucket['doc_count']
                message += f"  • {doc_type}: {count} case{'s' if count != 1 else ''}\n"
            message += "\n"

        # Show top cases
        display_count = min(top_n, len(hits))
        for i, hit in enumerate(hits[:display_count], 1):
            src = hit['_source']
            message += f"{i}. **{src.get('title', 'Untitled Case')}**\n"
            message += f"   Document Type: {src.get('document_type', 'N/A')}\n"
            message += f"   Category: {src.get('case_category', 'N/A')}\n"

            if src.get("outcome_summary"):
                summary = src['outcome_summary']
                if len(summary) > 150:
                    summary = summary[:150] + "..."
                message += f"   Outcome: {summary}\n"

            message += "\n"

        return message

    except Exception as e:
        return f"Error searching by court type: {str(e)}"


# ---------- Enhanced handler ----------
def topic_query_handler(user_input):
    """Wrapper for topics queries with enhanced functionality"""
    # Check for specific queries about document types or court types
    user_input_lower = user_input.lower()

    # Patterns to detect document type queries
    doc_type_patterns = [
        "document type", "doc type", "type of document",
        "judgment", "case", "ruling", "order", "motion"
    ]

    # Patterns to detect court type queries
    court_patterns = [
        "court type", "which court", "high court", "supreme court",
        "court of appeal", "magistrate", "district court"
    ]

    # Check if it's a document type query
    if any(pattern in user_input_lower for pattern in doc_type_patterns):
        # Extract potential document type from query
        for pattern in ["judgment", "case", "ruling", "order", "motion"]:
            if pattern in user_input_lower:
                return search_by_document_type(pattern.capitalize())

        # Default to searching all documents
        return search_by_document_type(user_input)

    # Check if it's a court type query
    elif any(pattern in user_input_lower for pattern in court_patterns):
        # Extract potential court type from query
        court_types = ["High Court", "Supreme Court", "Court of Appeal", "Magistrate Court", "District Court"]
        for court in court_types:
            if court.lower() in user_input_lower:
                return search_by_court_type(court)

        # Default to searching with the input as court type
        return search_by_court_type(user_input)

    # Regular topic search
    return search_topics(user_input)