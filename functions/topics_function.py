# topics_functions.py
import random
from rapidfuzz import process
from opensearchpy import exceptions
from config import client, index_name  # <--- use config here

# Random AI-style responses for different scenarios
AI_RESPONSES = {
    "found_cases": [
        "I've analyzed the legal database and found the following relevant cases:",
        "After searching through the case records, here are the most relevant findings:",
        "Based on my analysis of legal documents, here are the cases matching your query:",
        "I've reviewed the case law and found these relevant precedents:",
        "Here are the legal cases I found related to your topic of interest:"
    ],
    "no_results": [
        "I couldn't find any cases specifically addressing that topic in the database.",
        "No matching cases were found for that particular legal issue.",
        "After searching the legal records, I didn't find any cases related to that topic.",
        "The database doesn't contain any cases matching that specific query."
    ],
    "single_result": [
        "I found one relevant case in the legal records:",
        "There's one case that addresses this legal matter:",
        "One precedent case was found related to your query:"
    ],
    "multiple_results": [
        "I found several cases that might be relevant to your inquiry:",
        "There are multiple precedents addressing this legal topic:",
        "Several cases in the database relate to this issue:"
    ]
}


# ---------- Helper function to separate comma-separated values ----------
def separate_comma_values(text):
    """Separate comma-separated values in text and return as list"""
    if not text:
        return []

    # Split by comma and strip whitespace
    items = [item.strip() for item in text.split(',')]
    # Filter out empty strings
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
                    {"match": {"full_text": topic}}
                ]
            }
        },
        "size": top_n
    }

    try:
        response = client.search(index=index_name, body=search_body)
        hits = response['hits']['hits']
        total_hits = response['hits']['total']['value']

        # Start with a random AI-style introduction
        if not hits:
            return random.choice(AI_RESPONSES["no_results"])

        # Choose appropriate AI response based on number of results
        if total_hits == 1:
            intro = random.choice(AI_RESPONSES["single_result"])
        elif total_hits > 1:
            intro = random.choice(AI_RESPONSES["multiple_results"])
        else:
            intro = random.choice(AI_RESPONSES["found_cases"])

        message = f"{intro}\n\n"
        message += f"**Total Results:** {total_hits} case{'s' if total_hits != 1 else ''} related to '{topic}'\n\n"

        # Display top 5 (or fewer if less available)
        display_count = min(top_n, len(hits))

        for i, hit in enumerate(hits[:display_count], 1):
            src = hit['_source']

            # Determine case type
            case_type = src.get('case_type', 'Not specified')
            court_type = src.get('court_type', 'Not specified')

            # Check if it's an appeal
            is_appeal = False
            if src.get('full_text', '').lower().find('appeal') != -1:
                is_appeal = True
            elif src.get('title', '').lower().find('appeal') != -1:
                is_appeal = True
            elif 'appeal' in str(src.get('case_type', '')).lower():
                is_appeal = True

            # Format case type information
            if is_appeal:
                case_type_display = f"**Appeal Case** - {court_type}"
            else:
                case_type_display = f"**Case** - {court_type}"

            # Add specific case type if available
            if case_type and case_type != 'Not specified':
                case_type_display += f" ({case_type})"

            message += f"**{i}. {src.get('title', 'Untitled Case')}**\n"
            message += f"{case_type_display}\n"

            # Process and display people with comma separation
            if src.get("people"):
                message += "**People Involved:**\n"
                for p in src['people']:
                    name = p.get('name', 'Unknown')
                    role = p.get('role', 'Unknown role')

                    # Separate comma-separated names
                    separated_names = separate_comma_values(name)
                    if separated_names:
                        for separated_name in separated_names:
                            message += f"  • {separated_name} ({role})\n"
                    else:
                        message += f"  • {name} ({role})\n"

            # Show filtered points_simple containing the topic
            if src.get("points_simple"):
                message += "**Relevant Points (where '{topic}' appears):**\n"
                found_points = 0
                for pt in src['points_simple']:
                    # Check if topic appears in this point (case-insensitive)
                    if topic.lower() in pt.lower():
                        message += f"  • {pt}\n"
                        found_points += 1

                if found_points == 0:
                    # If no specific matches, show summary
                    message += f"  • Topic not explicitly mentioned in case points, but case is related to similar legal issues.\n"
                else:
                    message += f"\n  *{found_points} point{'s' if found_points != 1 else ''} specifically mention '{topic}'*\n"

            # Add outcome summary if available
            if src.get("outcome_summary"):
                message += f"\n**Outcome:** {src['outcome_summary']}\n"

            # Add result if available
            if src.get("result"):
                message += f"**Result:** {src['result']}\n"

            message += "\n" + "=" * 60 + "\n\n"

        return message

    except exceptions.ConnectionError:
        error_responses = [
            "I'm having trouble connecting to the legal database at the moment.",
            "There seems to be a connection issue with the case records system.",
            "I can't access the legal database due to connectivity problems."
        ]
        return random.choice(error_responses)
    except Exception as e:
        error_responses = [
            "An unexpected error occurred while searching the legal database.",
            "I encountered an issue while processing your legal research request.",
            "There was a problem retrieving the case information you requested."
        ]
        return f"{random.choice(error_responses)} Error details: {str(e)}"


# ---------- Handler ----------
def topic_query_handler(user_input):
    """Wrapper for topics queries"""
    # Add a small processing message
    processing_messages = [
        "Searching through legal precedents...",
        "Analyzing case law database...",
        "Reviewing legal documents...",
        "Processing your legal research query..."
    ]

    # The search_topics function will now return AI-style responses
    return search_topics(user_input)