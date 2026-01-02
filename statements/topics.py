# functions/topics_functions.py
import random
import re
from functions.topics_function import search_topics  # your actual topic search logic

# words to ignore (CODE-LEVEL, NOT AI)
IGNORE_WORDS = {"cases", "letters", "appeals"}

def clean_topics(text: str) -> str:
    """
    Remove ignored words ANYWHERE in the topic string.
    Keeps commas and multiple topics intact.
    """

    # normalize text (remove punctuation except commas)
    text = re.sub(r"[^\w\s,]", "", text.lower())

    parts = [p.strip() for p in text.split(",")]
    cleaned_parts = []

    for part in parts:
        words = part.split()
        words = [w for w in words if w not in IGNORE_WORDS]
        if words:
            cleaned_parts.append(" ".join(words))

    return ", ".join(cleaned_parts).strip()


def topics_query(user_input):
    """
    Process 'search:' and 'do not search:' queries.
    """
    input_lower = user_input.lower().strip()

    # Handle "search:" queries
    if input_lower.startswith("search:"):
        topics = input_lower[len("search:"):].strip()
        topics = clean_topics(topics)   # 🔥 FULL removal happens here

        if not topics:
            return "Please specify the topics to search. For example: 'search: mining, energy'"

        return search_topics(topics)

    # Handle "do not search:" queries
    elif input_lower.startswith("do not search:"):
        topics = input_lower[len("do not search:"):].strip()
        topics = clean_topics(topics)   # 🔥 FULL removal happens here

        if not topics:
            return "Please specify the topics you don't want me to search."

        responses = [
            f"Sure, I won't search for {topics}.",
            f"Okay, I will respect your request and not search for {topics}.",
            f"No problem, I won't provide any results for {topics}.",
            f"Understood, I won't search anything related to {topics}."
        ]
        return random.choice(responses)

    return None


def topics_query_handler(user_input):
    return topics_query(user_input)
