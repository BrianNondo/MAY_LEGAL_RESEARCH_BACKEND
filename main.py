from statements.who import who_query
from statements.what import what_query
from text_cleaner.clean_text import clean_user_text

def main():
    raw_input_text = input("Enter your query: ").strip()

    if not raw_input_text:
        print("Please enter a query.")
        return

    # ---------- CLEAN INPUT USING CHATGPT ----------
    try:
        cleaned_input = clean_user_text(raw_input_text)
        print(f"[CLEANED INPUT]: {cleaned_input}")  # <-- print cleaned text for testing
    except Exception as e:
        print("Text cleaning service unavailable. Using raw input.")
        cleaned_input = raw_input_text
        print(f"[RAW INPUT USED]: {cleaned_input}")

    # ---------- WHO ----------
    message = who_query(cleaned_input)
    if message:
        print("\n" + message)
        return

    # ---------- WHAT ----------
    message = what_query(cleaned_input)
    if message:
        print("\n" + message)
        return

    print("Sorry, I can only answer 'Who' or 'What' questions for now.")

if __name__ == "__main__":
    main()
