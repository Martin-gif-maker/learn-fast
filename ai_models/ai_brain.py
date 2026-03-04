import requests
import json


# --- 1. AUTO-DISCOVERY FUNCTION (Fixed Name) ---
def get_best_model(api_key):
    """Finds the best available model for your key."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    try:
        response = requests.get(url)
        if response.status_code != 200:
            # If we can't check, default to the most common one
            return "gemini-1.5-flash"

        data = response.json()
        # Filter for models that support generating content
        models = [m['name'].replace("models/", "") for m in data.get('models', []) if
                  'generateContent' in m.get('supportedGenerationMethods', [])]

        # Priority List: Try Flash first, then Pro
        for m in models:
            if "flash" in m and "8b" not in m: return m
        for m in models:
            if "pro" in m: return m

        # If list exists but no match, return first available
        return models[0] if models else "gemini-1.5-flash"
    except:
        return "gemini-1.5-flash"


# --- 2. CORE GOOGLE FUNCTION ---
def ask_google(api_key, prompt, system_instruction):
    if not api_key: return {"error": "API Key is missing."}

    # Now this call will work because the name matches above
    model = get_best_model(api_key)
    print(f"🚀 USING MODEL: {model}")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}

    data = {
        "contents": [{"parts": [{"text": prompt}]}],
        "system_instruction": {"parts": [{"text": system_instruction}]},
        "generationConfig": {"response_mime_type": "application/json"}
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code != 200: return {"error": f"Google refused: {response.status_code}"}

        result = response.json()
        if "candidates" not in result: return {"error": "AI returned no content."}

        text = result["candidates"][0]["content"]["parts"][0]["text"]
        text = text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)
    except Exception as e:
        return {"error": str(e)}


# --- HELPER FOR LANGUAGE ---
def get_lang_instruction(lang):
    if lang == 'bg':
        return " IMPORTANT: The content MUST be in BULGARIAN language. Keep the JSON keys in English, but the values in Bulgarian."
    return ""


# --- 3. FEATURE FUNCTIONS ---

def generate_flashcards(api_key, text, lang='en'):
    lang_note = get_lang_instruction(lang)
    sys_msg = f"Create 5 flashcards. Return strictly valid JSON: {{ \"flashcards\": [ {{\"question\": \"...\", \"answer\": \"...\", \"funny_note\": \"...\"}} ] }}{lang_note}"
    return ask_google(api_key, f"Make flashcards for: {text}", sys_msg)


def generate_quiz(api_key, text, lang='en'):
    lang_note = get_lang_instruction(lang)
    sys_msg = (
        f"Create a 5-question multiple choice test. "
        f"Each question must have ONE correct answer. "
        f"Return strictly valid JSON: "
        f"{{ \"quiz\": [ {{\"question\": \"...\", \"options\": [\"Option A\", \"Option B\", \"Option C\", \"Option D\"], \"correct_answer\": \"Exact text of correct option\", \"explanation\": \"...\"}} ] }}{lang_note}"
    )
    return ask_google(api_key, f"Create a test based on: {text}", sys_msg)


def simplify_text(api_key, text, lang='en'):
    lang_note = get_lang_instruction(lang)
    sys_msg = f"Rewrite the text to be very simple (ELI5) and funny. Return strictly valid JSON: {{ \"summary_title\": \"...\", \"simplified_content\": \"...\", \"key_points\": [\"...\", \"...\"] }}{lang_note}"
    return ask_google(api_key, f"Simplify this: {text}", sys_msg)