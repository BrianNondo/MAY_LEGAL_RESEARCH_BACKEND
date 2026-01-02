import os
from dotenv import load_dotenv
from openai import OpenAI

# Load .env
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None


def search_may(query: str) -> str:
    """
    AI-powered MAY Legal Assistant (About & Capabilities).
    Responds politely and naturally about itself.
    Does not answer legal questions.
    """
    if not query:
        return "I didn’t quite catch that. Could you please repeat?"

    if not client:
        return "MAY Legal Assistant is currently unavailable. Please check system configuration."

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are MAY Legal Research. "
                        "You should sound polite, calm, friendly, and human — never robotic. "
                        "You may respond to greetings and small talk naturally (e.g. 'How are you?'). "
                        "If asked anything beyond your current scope, kindly explain that you are still being developed. "
                        "Clearly and gently state that, for now, you can only help with searching legal names and cases. but still under development."
                        "Your tone should feel welcoming, professional, and respectful."
                    ),
                },
                {"role": "user", "content": query},
            ],
            temperature=1.0,  # more human
            max_tokens=300,
        )

        ai_message = response.choices[0].message.content.strip()

        return f"{ai_message}"

    except Exception as e:
        return "Something went wrong while responding. Please try again."
