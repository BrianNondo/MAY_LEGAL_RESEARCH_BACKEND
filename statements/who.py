import random
from functions.who_function import search_person

def who_query(user_input):
    """
    Process 'who is' and 'don't tell me about' queries.
    Returns search_person results for 'who is' or a polite refusal for 'don't tell me about'.
    """
    input_lower = user_input.lower().strip()

    # Handle "who is" queries
    if input_lower.startswith("who is "):
        name = input_lower[7:].strip()  # Remove "who is "

        if not name:
            return "Please specify a person's name. For example: 'who is Albert Einstein?'"

        # Remove common filler words
        filler_words = ["the", "a", "an", "mr", "mrs", "ms", "dr", "professor", "prof"]
        name_parts = name.split()
        if name_parts[0].lower() in filler_words:
            name = " ".join(name_parts[1:])

        return search_person(name)

    # Handle "don't tell me about" or "dont tell me about" queries
    elif input_lower.startswith("don't tell me about ") or input_lower.startswith("dont tell me about "):
        # Extract the name after the phrase
        if input_lower.startswith("don't tell me about "):
            name = input_lower[20:].strip()  # length of "don't tell me about "
        else:
            name = input_lower[19:].strip()  # length of "dont tell me about "

        if not name:
            return "Please specify what you don't want me to tell you about."

        # Random polite responses including the name
        responses = [
            f"Sure, I won't tell you about {name}.",
            f"Okay, I will respect your privacy and not share information about {name}.",
            f"No problem, I won't provide any details about {name}.",
            f"Understood, I won't tell you anything about {name}."
        ]
        return random.choice(responses)

    # If input doesn't match any recognized pattern
    return None

# Example handler that uses only who_query
def person_query_handler(user_input):
    return who_query(user_input)
