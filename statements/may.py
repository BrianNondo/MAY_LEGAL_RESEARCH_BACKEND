from functions.may_function import search_may  # <-- your function that processes the query

def may_query(user_input):
    """
    Process 'may_search:' queries.
    Extract the text after 'may_search:' and pass it to search_may to get the message.
    """

    input_lower = user_input.lower().strip()

    # Handle "may_search:" queries
    if input_lower.startswith("may_search:"):
        query = user_input[len("may_search:"):].strip()

        if not query:
            return "Please specify what you want me to search for."

        # Pass the extracted query to your function which returns the message
        return search_may(query)

    # If input doesn't match
    return None
