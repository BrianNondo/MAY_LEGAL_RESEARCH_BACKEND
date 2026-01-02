import random
from rapidfuzz import process
from opensearchpy import exceptions
from config import client, index_name  # <--- use config here


# ---------- Updated search_person (focused on person info) ----------
def search_person(name, top_n=5):
    """Search OpenSearch for a person and return ONLY person information"""
    search_body = {
        "query": {
            "nested": {"path": "people", "query": {"match": {"people.name": name}}}
        },
        "size": top_n
    }

    try:
        response = client.search(index=index_name, body=search_body)
        hits = response['hits']['hits']
        if not hits:
            return f"No cases found for '{name}'."

        # Collect all person occurrences
        person_occurrences = []
        for hit in hits:
            src = hit['_source']
            source_url = src.get("source_url", "unknown")  # Changed to source_url
            for p in src.get("people", []):
                # Use fuzzy matching to catch variations
                if process.extractOne(name, [p.get("name", "")])[1] >= 80:  # 80% match threshold
                    person_occurrences.append({
                        "name": p["name"],
                        "role": p["role"],
                        "identity_type": p.get("identity_type", "Unknown"),
                        "title": src.get("title"),
                        "court_type": src.get("court_type"),
                        "case_type": src.get("case_type"),
                        "source_url": source_url  # Changed to source_url
                    })

        if not person_occurrences:
            return f"No person named '{name}' found in any cases."

        if len(person_occurrences) == 1:
            person = person_occurrences[0]
            message = f"I found {len(person_occurrences)} record of {person['name']}. "
            message += f"{person['name']} served as {person['role']} ({person['identity_type']}) "
            message += f"in the case '{person['title']}', which was a {person['case_type']} matter "
            message += f"at {person['court_type']}. Source URL: {person['source_url']}"  # Changed to source_url
        else:
            message = f"There are {len(person_occurrences)} records of people named '{name}' in our database.\n\n"

            # Group by case to show organized information
            cases_by_person = {}
            for person in person_occurrences:
                case_key = person['title']
                if case_key not in cases_by_person:
                    cases_by_person[case_key] = []
                cases_by_person[case_key].append(person)

            for i, (case_title, persons_in_case) in enumerate(cases_by_person.items(), 1):
                message += f"{i}. In the case '{case_title}':\n"
                for person in persons_in_case:
                    message += f"   • {person['name']} was {person['role']} ({person['identity_type']})\n"
                message += f"   Court: {persons_in_case[0]['court_type']} | Case Type: {persons_in_case[0]['case_type']}\n"
                message += f"   Source URL: {persons_in_case[0]['source_url']}\n\n"  # Changed to source_url

        return message

    except exceptions.ConnectionError:
        return "ERROR: Connection lost during search."
    except Exception as e:
        return f"ERROR: {e}"


# ---------- AI-style search_person ----------
RESPONSES_SINGLE = [
    "I found {count} record of {name} in our database. {name} served as {role} ({identity_type}) in the case '{title}', which was a {case_type} matter at {court_type}. Source URL: {source_url}",  # Changed to source_url
    "There is {count} person named {name} in our records. Their role was {role} ({identity_type}) in the case titled '{title}', a {case_type} proceeding at {court_type}. Source URL: {source_url}",  # Changed to source_url
    "I located {count} entry for {name}. They were {role} ({identity_type}) in the case '{title}', handled by {court_type} as a {case_type} case. Source URL: {source_url}",  # Changed to source_url
]

RESPONSES_MULTIPLE = [
    "There are {count} individuals named {name} in our database. For example, {example_name} was {role} ({identity_type}) in the case '{title}' at {court_type} ({case_type}). Source URL: {source_url}",  # Changed to source_url
    "I found {count} records for people named {name}. One instance shows {example_name} as {role} ({identity_type}) in the {case_type} case titled '{title}' at {court_type}. Source URL: {source_url}",  # Changed to source_url
    "Multiple entries exist for {name} - {count} in total. In one case, {example_name} served as {role} ({identity_type}) in '{title}' ({case_type}) at {court_type}. Source URL: {source_url}",  # Changed to source_url
]


def search_person_ai(name, top_n=5):
    """AI-style search with fuzzy matching - returns ONLY person information"""
    search_body = {
        "query": {"nested": {"path": "people", "query": {"match_all": {}}}},
        "size": 100
    }

    try:
        response = client.search(index=index_name, body=search_body)
        hits = response['hits']['hits']
        if not hits:
            return f"Sorry, I couldn't find any cases mentioning '{name}'."

        # Collect all people with complete information
        all_people = []
        for hit in hits:
            src = hit['_source']
            source_url = src.get("source_url", "unknown")  # Changed to source_url
            for p in src.get("people", []):
                all_people.append({
                    "name": p["name"],
                    "role": p["role"],
                    "identity_type": p.get("identity_type", "Unknown"),
                    "title": src.get("title"),
                    "court_type": src.get("court_type"),
                    "case_type": src.get("case_type"),
                    "source_url": source_url  # Changed to source_url
                })

        people_names = [p["name"] for p in all_people]
        best_match, score = process.extractOne(name, people_names)

        if score < 60:
            return f"No cases found for '{name}'."

        matching_people = [p for p in all_people if p["name"] == best_match]

        if len(matching_people) == 1:
            person = matching_people[0]
            message = random.choice(RESPONSES_SINGLE).format(
                count="one",
                name=person["name"],
                role=person["role"],
                identity_type=person["identity_type"],
                title=person["title"],
                court_type=person["court_type"],
                case_type=person["case_type"],
                source_url=person["source_url"]  # Changed to source_url
            )
        else:
            example = random.choice(matching_people)
            message = random.choice(RESPONSES_MULTIPLE).format(
                count=len(matching_people),
                name=best_match,
                example_name=example["name"],
                role=example["role"],
                identity_type=example["identity_type"],
                title=example["title"],
                court_type=example["court_type"],
                case_type=example["case_type"],
                source_url=example["source_url"]  # Changed to source_url
            )

        # Add summary of additional matches if there are more
        if len(matching_people) > 1:
            message += f"\n\nOther roles for {best_match} include:"
            # Show unique roles/titles
            shown_titles = set([example['title']])
            shown_count = 0
            for person in matching_people:
                if person['title'] not in shown_titles and shown_count < 3:
                    message += f"\n• {person['role']} ({person['identity_type']}) in '{person['title']}'"
                    shown_titles.add(person['title'])
                    shown_count += 1

        return message

    except exceptions.ConnectionError:
        return "ERROR: Connection lost during search."
    except Exception as e:
        return f"ERROR: {e}"


# ---------- search_case (for general case searches) ----------
def search_case(query_text, top_n=5):
    """Search OpenSearch for general cases"""
    search_body = {
        "query": {
            "bool": {
                "should": [
                    {"match": {"title": query_text}},
                    {"match": {"keywords": query_text}},
                    {"match": {"entities": query_text}},
                    {"match": {"points_simple": query_text}},
                    {"match": {"full_text": query_text}},
                    {"nested": {"path": "people", "query": {"match": {"people.name": query_text}}}}
                ]
            }
        },
        "size": top_n
    }

    try:
        response = client.search(index=index_name, body=search_body)
        hits = response['hits']['hits']
        if not hits:
            return f"No cases found for '{query_text}'."

        message = f"Top {len(hits)} cases for '{query_text}':\n"
        for hit in hits:
            src = hit['_source']
            message += f"- {src.get('title')} (Case ID: {hit['_id']})\n"
            if src.get("points_simple"):
                message += "  Points:\n"
                for pt in src['points_simple']:
                    message += f"    - {pt}\n"
            if src.get("people"):
                message += "  People in case:\n"
                for p in src['people']:
                    message += f"    * {p['name']} ({p['role']})\n"
            message += f"  Outcome: {src.get('outcome_summary')}\n\n"
        return message
    except exceptions.ConnectionError:
        return "ERROR: Connection lost during search."
    except Exception as e:
        return f"ERROR: {e}"