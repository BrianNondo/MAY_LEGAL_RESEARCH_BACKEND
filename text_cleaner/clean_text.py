# utils/openai_cleaner.py
import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from .env file in parent directory
load_dotenv()  # This will automatically load .env from parent folder

# Initialize the OpenAI client with API key from .env
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Check if API key is loaded
if not os.getenv("OPENAI_API_KEY"):
    print("⚠️  Warning: OPENAI_API_KEY not found in .env file")
    client = None

SYSTEM_PROMPT = """
You are MAY, a text cleaning assistant.

TASK:
- Rewrite user input into clear, correct English.
- Fix spelling, grammar, and abbreviations.
- Keep proper names exactly as they are.
- If the user asks any question related to MAY Legal Research or you, output ONLY:
    - may_search: <user question>
- Determine if the user strictly wants to know about a person:
    - If yes, start the cleaned text with "who is".
    - if the user does not strictly want to know about a person, start the cleaned text with "don't tell me about".
- Determine if the user wants to know about a topic:
    - Extract only the key points (main nouns or keywords).
    - For example, "cases related to mining and energy" -> "mining, energy, cases".
    - If yes, start the cleaned text with "search: ".
    - Only use "do not search: " if the user clearly says not to search.
- Do NOT answer the question or add new information.
- Output ONLY the cleaned text.
- return exact user input if nothing matches.
"""




def clean_user_text(user_text: str) -> str:
    """Clean user input using OpenAI"""
    if client is None:
        # Fallback: simple cleaning if OpenAI is not configured
        return user_text.strip().lower()

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_text}
            ],
            temperature=1.0,
            max_tokens=300
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"⚠️  OpenAI error: {e}")
        # Fallback to original text
        return user_text.strip()


