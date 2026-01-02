# who_functions.py
import random
from rapidfuzz import process, fuzz
from opensearchpy import exceptions
from config import client, index_name

# AI-style responses for no results
NO_RESULTS_RESPONSES = [
    "I searched through all the cases in our database, but I couldn't find anyone named '{name}'. Could you try a different spelling or provide more details?",
    "Hmm, I don't see any records for '{name}' in our legal database. Perhaps the name is spelled differently or they might be listed under another variation?",
    "I've looked everywhere, but there's no match for '{name}' in our case records. Would you like to try searching with just the last name?",
    "Sorry, I couldn't locate anyone named '{name}' in our system. Sometimes names appear differently in legal documents - maybe try a different format?",
]


def normalize_name(name):
    """
    Normalize a name for better matching:
    - Convert to lowercase
    - Remove all punctuation (periods, commas, hyphens)
    - Replace multiple spaces with single space
    - Strip leading/trailing spaces

    Examples:
        "J.M. Chimembe" -> "j m chimembe"
        "Stuart Sikazwe" -> "stuart sikazwe"
        "B. Mulunda" -> "b mulunda"
    """
    if not name:
        return ""

    # Convert to lowercase
    normalized = name.lower()

    # Remove common punctuation
    for char in ['.', ',', '-', "'", '"']:
        normalized = normalized.replace(char, ' ')

    # Replace multiple spaces with single space and strip
    normalized = ' '.join(normalized.split())

    return normalized


# ---------- Universal search_person (works for ALL name formats) ----------
def search_person(name, top_n=5):
    """
    Universal person search with client-side fuzzy matching.
    Works for: full names, partial names, initials, surnames only.
    """

    # Normalize the search name
    normalized_search_name = normalize_name(name)

    # Get ALL documents (most reliable approach)
    search_body = {
        "query": {"match_all": {}},
        "size": 1000  # Adjust based on your database size
    }

    try:
        response = client.search(index=index_name, body=search_body)
        hits = response['hits']['hits']

        if not hits:
            return random.choice(NO_RESULTS_RESPONSES).format(name=name)

        # Collect ALL people from all cases
        all_people = []
        for hit in hits:
            src = hit['_source']
            source_url = src.get("source_url", "unknown")
            for p in src.get("people", []):
                person_name = p.get("name", "")
                if person_name:  # Only add if name exists
                    all_people.append({
                        "name": person_name,
                        "normalized_name": normalize_name(person_name),
                        "role": p.get("role", "Unknown"),
                        "identity_type": p.get("identity_type", "Unknown"),
                        "title": src.get("title", "Unknown"),
                        "court_type": src.get("court_type", "Unknown"),
                        "case_type": src.get("case_type", "Unknown"),
                        "source_url": source_url
                    })

        if not all_people:
            return random.choice(NO_RESULTS_RESPONSES).format(name=name)

        # STEP 1: Try exact match first (case-insensitive)
        exact_matches = [p for p in all_people if p["normalized_name"] == normalized_search_name]

        if exact_matches:
            # Exact match found!
            best_normalized_name = normalized_search_name
            match_score = 100
            person_occurrences = exact_matches
        else:
            # STEP 2: Try fuzzy matching on normalized names
            normalized_names = [p["normalized_name"] for p in all_people]

            # Get multiple potential matches
            matches = process.extract(
                normalized_search_name,
                normalized_names,
                scorer=fuzz.token_sort_ratio,
                limit=20
            )

            # Filter matches with score >= 70 (increased threshold for better accuracy)
            good_matches = [match for match in matches if match[1] >= 70]

            if good_matches:
                # Get the best matching normalized name from fuzzy matches
                best_normalized_name = good_matches[0][0]
                match_score = good_matches[0][1]
                person_occurrences = [p for p in all_people if p["normalized_name"] == best_normalized_name]
            else:
                # STEP 3: Try substring/partial matching
                name_parts = normalized_search_name.split()
                if len(name_parts) > 0:
                    partial_matches = []
                    for person in all_people:
                        person_normalized = person["normalized_name"]
                        # Check if ALL search terms appear as substrings in the name
                        if all(search_part in person_normalized for search_part in name_parts):
                            partial_matches.append(person)

                    if partial_matches:
                        # Get unique names from partial matches
                        unique_names = {}
                        for p in partial_matches:
                            norm_name = p["normalized_name"]
                            if norm_name not in unique_names:
                                unique_names[norm_name] = p["name"]

                        # If exactly one unique person found, use that person
                        if len(unique_names) == 1:
                            best_normalized_name = list(unique_names.keys())[0]
                            match_score = 65
                            person_occurrences = [p for p in all_people if p["normalized_name"] == best_normalized_name]
                        # If multiple people found, suggest them
                        elif len(unique_names) <= 5:
                            suggestion = ", ".join(unique_names.values())
                            return f"I couldn't find an exact match for '{name}', but I found these similar names: {suggestion}. Would you like to search for one of these?"
                        else:
                            return random.choice(NO_RESULTS_RESPONSES).format(name=name)
                    else:
                        # STEP 4: Last resort - try matching any single word
                        any_word_matches = []
                        for person in all_people:
                            person_normalized = person["normalized_name"]
                            # Check if ANY search term appears as substring
                            if any(search_part in person_normalized for search_part in name_parts):
                                any_word_matches.append(person)

                        if any_word_matches:
                            unique_names = {}
                            for p in any_word_matches:
                                norm_name = p["normalized_name"]
                                if norm_name not in unique_names:
                                    unique_names[norm_name] = p["name"]

                            if len(unique_names) <= 10:
                                suggestion = ", ".join(list(unique_names.values())[:10])
                                return f"I couldn't find an exact match for '{name}', but I found these people with similar names: {suggestion}. Would you like to search for one of these?"

                        return random.choice(NO_RESULTS_RESPONSES).format(name=name)
                else:
                    return random.choice(NO_RESULTS_RESPONSES).format(name=name)

        # Use the original (non-normalized) name for display
        display_name = person_occurrences[0]["name"]

        # Build AI response
        if len(person_occurrences) == 1:
            person = person_occurrences[0]
            message = f"I found 1 record of {person['name']}"

            # Add note if search name doesn't match exactly
            if match_score < 100:
                message += f" (you searched for '{name}')"

            message += f". {person['name']} served as {person['role']} ({person['identity_type']}) "
            message += f"in the case '{person['title']}', which was a {person['case_type']} matter "
            message += f"at {person['court_type']}.\n\nSource URL: {person['source_url']}"
        else:
            message = f"I found {len(person_occurrences)} records of {display_name}"

            # Add note if search name doesn't match exactly
            if match_score < 100:
                message += f" (you searched for '{name}')"

            message += " in our database.\n\n"

            # Group by case
            cases_by_title = {}
            for person in person_occurrences:
                case_key = person['title']
                if case_key not in cases_by_title:
                    cases_by_title[case_key] = []
                cases_by_title[case_key].append(person)

            for i, (case_title, persons_in_case) in enumerate(cases_by_title.items(), 1):
                message += f"{i}. In the case '{case_title}':\n"
                for person in persons_in_case:
                    message += f"   • {person['name']} was {person['role']} ({person['identity_type']})\n"
                message += f"   Court: {persons_in_case[0]['court_type']} | Case Type: {persons_in_case[0]['case_type']}\n"
                message += f"   Source URL: {persons_in_case[0]['source_url']}\n\n"

        return message

    except exceptions.ConnectionError:
        return "I'm having trouble connecting to the database right now. Please try again in a moment."
    except Exception as e:
        return f"Oops, something went wrong while searching: {str(e)}"


# ---------- AI-style search_person ----------
RESPONSES_SINGLE = [
    "I found 1 record of {name} in our database. {name} served as {role} ({identity_type}) in the case '{title}', which was a {case_type} matter at {court_type}. Source URL: {source_url}",
    "There is 1 person named {name} in our records. Their role was {role} ({identity_type}) in the case titled '{title}', a {case_type} proceeding at {court_type}. Source URL: {source_url}",
    "I located 1 entry for {name}. They were {role} ({identity_type}) in the case '{title}', handled by {court_type} as a {case_type} case. Source URL: {source_url}",
]

RESPONSES_MULTIPLE = [
    "There are {count} individuals named {name} in our database. For example, {example_name} was {role} ({identity_type}) in the case '{title}' at {court_type} ({case_type}). Source URL: {source_url}",
    "I found {count} records for people named {name}. One instance shows {example_name} as {role} ({identity_type}) in the {case_type} case titled '{title}' at {court_type}. Source URL: {source_url}",
    "Multiple entries exist for {name} - {count} in total. In one case, {example_name} served as {role} ({identity_type}) in '{title}' ({case_type}) at {court_type}. Source URL: {source_url}",
]


def search_person_ai(name, top_n=5):
    """AI-style search with natural language responses"""

    # Normalize the search name
    normalized_search_name = normalize_name(name)

    # Get ALL documents for comprehensive matching
    search_body = {
        "query": {"match_all": {}},
        "size": 1000
    }

    try:
        response = client.search(index=index_name, body=search_body)
        hits = response['hits']['hits']

        if not hits:
            return random.choice(NO_RESULTS_RESPONSES).format(name=name)

        # Collect all people with normalized names
        all_people = []
        for hit in hits:
            src = hit['_source']
            source_url = src.get("source_url", "unknown")
            for p in src.get("people", []):
                person_name = p.get("name", "")
                if person_name:
                    all_people.append({
                        "name": person_name,
                        "normalized_name": normalize_name(person_name),
                        "role": p.get("role", "Unknown"),
                        "identity_type": p.get("identity_type", "Unknown"),
                        "title": src.get("title", "Unknown"),
                        "court_type": src.get("court_type", "Unknown"),
                        "case_type": src.get("case_type", "Unknown"),
                        "source_url": source_url
                    })

        if not all_people:
            return random.choice(NO_RESULTS_RESPONSES).format(name=name)

        # STEP 1: Try exact match first
        exact_matches = [p for p in all_people if p["normalized_name"] == normalized_search_name]

        if exact_matches:
            best_match = normalized_search_name
            score = 100
            matching_people = exact_matches
        else:
            # STEP 2: Fuzzy match on normalized names
            normalized_names = [p["normalized_name"] for p in all_people]
            fuzzy_result = process.extractOne(
                normalized_search_name,
                normalized_names,
                scorer=fuzz.token_sort_ratio
            )

            if fuzzy_result:
                best_match, score = fuzzy_result
            else:
                score = 0
                best_match = None

            if score >= 70:
                matching_people = [p for p in all_people if p["normalized_name"] == best_match]
            else:
                # STEP 3: Try substring matching
                name_parts = normalized_search_name.split()
                if len(name_parts) > 0:
                    partial = []
                    for person in all_people:
                        person_normalized = person["normalized_name"]
                        # Check if ALL search terms appear as substrings
                        if all(search_part in person_normalized for search_part in name_parts):
                            partial.append(person)

                    if partial:
                        unique = {}
                        for p in partial:
                            norm_name = p["normalized_name"]
                            if norm_name not in unique:
                                unique[norm_name] = p["name"]

                        # If exactly one unique person, use them
                        if len(unique) == 1:
                            best_match = list(unique.keys())[0]
                            score = 65
                            matching_people = [p for p in all_people if p["normalized_name"] == best_match]
                        # If multiple people, suggest them
                        elif len(unique) <= 5:
                            return f"No exact match for '{name}', but found: {', '.join(unique.values())}. Try one of these?"
                        else:
                            return random.choice(NO_RESULTS_RESPONSES).format(name=name)
                    else:
                        # STEP 4: Try matching any single word
                        any_word = []
                        for person in all_people:
                            person_normalized = person["normalized_name"]
                            if any(search_part in person_normalized for search_part in name_parts):
                                any_word.append(person)

                        if any_word:
                            unique = {}
                            for p in any_word:
                                norm_name = p["normalized_name"]
                                if norm_name not in unique:
                                    unique[norm_name] = p["name"]

                            if len(unique) <= 10:
                                suggestion = ", ".join(list(unique.values())[:10])
                                return f"No exact match for '{name}', but found similar: {suggestion}. Try one of these?"

                        return random.choice(NO_RESULTS_RESPONSES).format(name=name)
                else:
                    return random.choice(NO_RESULTS_RESPONSES).format(name=name)

        display_name = matching_people[0]["name"]

        if len(matching_people) == 1:
            person = matching_people[0]
            message = random.choice(RESPONSES_SINGLE).format(
                name=person["name"],
                role=person["role"],
                identity_type=person["identity_type"],
                title=person["title"],
                court_type=person["court_type"],
                case_type=person["case_type"],
                source_url=person["source_url"]
            )
        else:
            example = random.choice(matching_people)
            message = random.choice(RESPONSES_MULTIPLE).format(
                count=len(matching_people),
                name=display_name,
                example_name=example["name"],
                role=example["role"],
                identity_type=example["identity_type"],
                title=example["title"],
                court_type=example["court_type"],
                case_type=example["case_type"],
                source_url=example["source_url"]
            )

            # Add summary of additional matches
            if len(matching_people) > 1:
                message += f"\n\nOther roles for {display_name} include:"
                shown_titles = set([example['title']])
                shown_count = 0
                for person in matching_people:
                    if person['title'] not in shown_titles and shown_count < 3:
                        message += f"\n• {person['role']} ({person['identity_type']}) in '{person['title']}'"
                        shown_titles.add(person['title'])
                        shown_count += 1

        return message

    except exceptions.ConnectionError:
        return "I'm having trouble connecting to the database right now. Please try again in a moment."
    except Exception as e:
        return f"Oops, something went wrong while searching: {str(e)}"


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
            return f"I couldn't find any cases matching '{query_text}'. Try using different keywords or a more specific search term."

        message = f"I found {len(hits)} cases related to '{query_text}':\n\n"
        for i, hit in enumerate(hits, 1):
            src = hit['_source']
            message += f"{i}. {src.get('title')} (Case ID: {hit['_id']})\n"
            if src.get("points_simple"):
                message += "   Key Points:\n"
                for pt in src['points_simple'][:3]:  # Limit to 3 points
                    message += f"   - {pt}\n"
            if src.get("people"):
                message += "   People involved:\n"
                for p in src['people'][:3]:  # Limit to 3 people
                    message += f"   * {p.get('name', 'Unknown')} ({p.get('role', 'Unknown')})\n"
            if src.get('outcome_summary'):
                message += f"   Outcome: {src.get('outcome_summary')}\n"
            message += "\n"
        return message

    except exceptions.ConnectionError:
        return "I'm having trouble connecting to the database right now. Please try again in a moment."
    except Exception as e:
        return f"Oops, something went wrong while searching: {str(e)}"