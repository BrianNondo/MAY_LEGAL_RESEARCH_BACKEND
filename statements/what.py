from functions.people import search_case

def what_query(user_input):
    """
    Only process if 'what' is in the input.
    Returns the message from people.py
    """
    if "what" not in user_input.lower():
        return None

    return search_case(user_input)
