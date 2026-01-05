import random
import json
from datetime import datetime

from statements.who import who_query
from statements.may import may_query        # <-- add this
# from statements.what import what_query
from statements.topics import topics_query
from text_cleaner.clean_text import clean_user_text
from functions.fetch_file import fetch_file

APOLOGY_RESPONSES = [
    "Sorry about that — I’m still adding some features. I’ll be able to help more soon.",
    "I can’t fully help with that yet. I’m still under development, but I’m improving.",
    "Apologies, I don’t support that request just yet. More features are coming.",
    "I’m not quite able to answer that right now. Some parts of me are still being built.",
    "Sorry, that’s not something I can handle at the moment — but I’ll get there.",
    "I’m still learning and don’t have that feature yet. Thanks for your patience.",
    "I can’t answer that properly for now. I’m still being improved.",
    "That’s a bit outside what I can do right now. More capabilities are on the way."
]

FAILED_LOG_JSON = "failed_queries.json"


def log_failed_query_json(query: str):
    """Append failed queries to a JSON file"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = {"timestamp": timestamp, "query": query}

    try:
        # Load existing data if file exists
        try:
            with open(FAILED_LOG_JSON, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            data = []

        # Append new entry
        data.append(entry)

        # Save back to file
        with open(FAILED_LOG_JSON, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Error logging failed query: {e}")


def handle_query(raw_input_text: str):
    if not raw_input_text:
        return None, "Please enter a query."

    # ---------- GET FILE (FAKE RESPONSE ONLY) ----------
    if "get_file:" in raw_input_text.lower():
        response = fetch_file(raw_input_text)
        return raw_input_text, response

    # ---------- CLEAN INPUT ----------
    try:
        cleaned_input = clean_user_text(raw_input_text)
    except Exception:
        cleaned_input = raw_input_text

    # ---------- WHO ----------
    message = who_query(cleaned_input)
    if message:
        return cleaned_input, message

    # ---------- MAY ----------
    message = may_query(cleaned_input)
    if message:
        return cleaned_input, message

    # ---------- TOPICS ----------
    message = topics_query(cleaned_input)
    if message:
        return cleaned_input, message

    # ---------- FALLBACK ----------
    log_failed_query_json(cleaned_input)
    return cleaned_input, random.choice(APOLOGY_RESPONSES)



def main():
    raw_input_text = input("Enter your query: ").strip()
    cleaned, response = handle_query(raw_input_text)

    if cleaned:
        print(f"[CLEANED INPUT]: {cleaned}")
    print("\n" + response)


if __name__ == "__main__":
    main()
