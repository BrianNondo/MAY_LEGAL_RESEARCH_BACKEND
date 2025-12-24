# main.py
import random
from datetime import datetime

from statements.who import who_query
from statements.what import what_query
from statements.topics import topics_query
from text_cleaner.clean_text import clean_user_text


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

FAILED_LOG_FILE = "failed_queries.txt"


def log_failed_query(query: str):
    """Append failed queries to a text file"""
    with open(FAILED_LOG_FILE, "a", encoding="utf-8") as f:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"[{timestamp}] {query}\n")


def handle_query(raw_input_text: str):
    if not raw_input_text:
        return None, "Please enter a query."

    # ---------- CLEAN INPUT ----------
    try:
        cleaned_input = clean_user_text(raw_input_text)
    except Exception:
        cleaned_input = raw_input_text

    # ---------- WHO ----------
    message = who_query(cleaned_input)
    if message:
        return cleaned_input, message

    # ---------- WHAT ----------
    message = what_query(cleaned_input)
    if message:
        return cleaned_input, message

    # ---------- TOPICS ----------
    message = topics_query(cleaned_input)
    if message:
        return cleaned_input, message

    # ---------- FALLBACK ----------
    log_failed_query(cleaned_input)
    return cleaned_input, random.choice(APOLOGY_RESPONSES)


def main():
    raw_input_text = input("Enter your query: ").strip()
    cleaned, response = handle_query(raw_input_text)

    if cleaned:
        print(f"[CLEANED INPUT]: {cleaned}")
    print("\n" + response)


if __name__ == "__main__":
    main()
