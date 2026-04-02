import requests
import json


# --- CORE GROQ FUNCTION ---
def ask_groq(api_key, prompt, system_instruction):
    if not api_key:
        return {"error": "API Key is missing. Check your .env file."}

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": prompt}
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.7
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)

        if response.status_code == 401:
            return {"error": "Invalid API key. Check your .env file."}
        if response.status_code == 429:
            return {"error": "Rate limit hit. Try again in a moment."}
        if response.status_code != 200:
            return {"error": f"Groq API error: {response.status_code}"}

        result = response.json()

        if "choices" not in result or not result["choices"]:
            return {"error": "Groq returned no content."}

        text = result["choices"][0]["message"]["content"].strip()
        text = text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)

    except requests.Timeout:
        return {"error": "Request timed out. Try again."}
    except json.JSONDecodeError:
        return {"error": "AI returned invalid JSON. Try again."}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


# --- LANGUAGE HELPER ---
def get_lang_instruction(lang):
    if lang == 'bg':
        return " IMPORTANT: All content values MUST be in BULGARIAN language. Keep JSON keys in English, but all values in Bulgarian."
    return ""


# --- FEATURE FUNCTIONS ---

def generate_flashcards(api_key, text, lang='en'):
    lang_note = get_lang_instruction(lang)
    system = (
        f"You are a study assistant. Create exactly 5 flashcards from the given text. "
        f"Return ONLY valid JSON in this exact format: "
        f'{{ "flashcards": [ {{"question": "...", "answer": "...", "funny_note": "..."}} ] }}'
        f"{lang_note}"
    )
    return ask_groq(api_key, f"Create flashcards for this text:\n\n{text}", system)


def generate_quiz(api_key, text, lang='en'):
    lang_note = get_lang_instruction(lang)
    system = (
        f"You are a quiz generator. Create exactly 5 multiple choice questions from the given text. "
        f"Each question must have exactly 4 options and one correct answer. "
        f"Return ONLY valid JSON in this exact format: "
        f'{{ "quiz": [ {{"question": "...", "options": ["A", "B", "C", "D"], "correct_answer": "exact text of correct option", "explanation": "..."}} ] }}'
        f"{lang_note}"
    )
    return ask_groq(api_key, f"Create a quiz based on this text:\n\n{text}", system)


def simplify_text(api_key, text, lang='en'):
    lang_note = get_lang_instruction(lang)
    system = (
        f"You are a study assistant. Simplify the given text so a 12-year-old can understand it. "
        f"Make it clear, engaging, and slightly fun. "
        f"Return ONLY valid JSON in this exact format: "
        f'{{ "summary_title": "...", "simplified_content": "...", "key_points": ["point 1", "point 2", "point 3"] }}'
        f"{lang_note}"
    )
    return ask_groq(api_key, f"Simplify this text:\n\n{text}", system)