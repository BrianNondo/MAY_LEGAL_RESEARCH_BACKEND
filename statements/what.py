# functions/may_function.py

def search_may(query):
    """
    Simply returns a message with the user's query.
    """

    if not query:
        return "No message provided."

    return f"user said {query}"
