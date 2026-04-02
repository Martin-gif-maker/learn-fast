import os
import sys
import sqlite3
import random
import smtplib
import hashlib
from email.message import EmailMessage
from flask import Flask, request, jsonify, send_from_directory, session
from flask_cors import CORS
from dotenv import load_dotenv

# --- LOAD ENVIRONMENT VARIABLES ---
load_dotenv()
API_KEY = os.getenv("GROQ_API_KEY")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")
SECRET_KEY = os.getenv("SECRET_KEY", "fallback-secret-key")

# --- PATH SETUP ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AI_FOLDER = os.path.join(BASE_DIR, 'ai_models')
sys.path.append(AI_FOLDER)

# Try to import AI brain
try:
    from ai_brain import generate_flashcards, generate_quiz, simplify_text
except ImportError:
    try:
        from ai_models.ai_brain import generate_flashcards, generate_quiz, simplify_text
    except ImportError:
        print("⚠️ WARNING: Could not find 'ai_brain.py'. AI features will not work.")
        def generate_flashcards(k, t, l): return {"error": "AI module not found"}
        def generate_quiz(k, t, l): return {"error": "AI module not found"}
        def simplify_text(k, t, l): return {"error": "AI module not found"}

app = Flask(__name__)
app.secret_key = SECRET_KEY
CORS(app, supports_credentials=True)

# --- DATABASE ---
DB_FILE = os.path.join(BASE_DIR, "learnfast.db")

def hash_password(password):
    """Hash a password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            xp INTEGER DEFAULT 0,
            level INTEGER DEFAULT 1
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# --- EMAIL ---
verification_codes = {}

def send_code_via_email(to_email, code):
    if not SENDER_EMAIL or not SENDER_PASSWORD:
        print(f"⚠️ Email not configured. CODE FOR {to_email}: {code}")
        return True  # Still allow registration during dev

    msg = EmailMessage()
    msg['Subject'] = "🚀 Learn Fast - Verification Code"
    msg['From'] = SENDER_EMAIL
    msg['To'] = to_email
    msg.set_content(f"Your Learn Fast verification code is: {code}\n\nThis code expires in 10 minutes.")

    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"❌ Email Error: {e}")
        print(f"⚠️ CODE FOR {to_email}: {code}")  # Fallback for dev
        return False

# --- STATIC ROUTES ---
@app.route('/')
def home():
    return send_from_directory(BASE_DIR, 'First_page.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory(BASE_DIR, filename)

# --- AUTH ROUTES ---
@app.route('/api/send-code', methods=['POST'])
def send_verification_code():
    data = request.json
    email = data.get('email', '').strip().lower()

    if not email:
        return jsonify({"error": "Email is required"}), 400

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    if cursor.fetchone():
        conn.close()
        return jsonify({"error": "Email already registered!"}), 400
    conn.close()

    code = str(random.randint(100000, 999999))
    verification_codes[email] = code

    send_code_via_email(email, code)
    return jsonify({"message": "Code sent"})

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    email = data.get('email', '').strip().lower()
    name = data.get('name', '').strip()
    password = data.get('password', '')
    code = data.get('code', '')

    # Input validation
    if not all([email, name, password, code]):
        return jsonify({"error": "All fields are required"}), 400

    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400

    if email not in verification_codes or verification_codes[email] != code:
        return jsonify({"error": "Invalid or expired code!"}), 400

    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
            (name, email, hash_password(password))
        )
        conn.commit()
        conn.close()
        del verification_codes[email]
        return jsonify({"message": "Account created successfully"})
    except sqlite3.IntegrityError:
        return jsonify({"error": "Email already registered!"}), 400
    except Exception as e:
        print(f"Registration error: {e}")
        return jsonify({"error": "Server error during registration"}), 500

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM users WHERE email = ? AND password = ?",
        (email, hash_password(password))
    )
    user = cursor.fetchone()
    conn.close()

    if user:
        session['user_id'] = user[0]
        return jsonify({
            "message": "Success",
            "user": {
                "id": user[0],
                "name": user[1],
                "xp": user[4],
                "level": user[5]
            }
        })
    return jsonify({"error": "Invalid email or password"}), 401

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({"message": "Logged out"})

@app.route('/api/update-xp', methods=['POST'])
def update_xp():
    data = request.json
    user_id = data.get('user_id')
    xp_gained = data.get('xp')

    if not user_id or xp_gained is None:
        return jsonify({"error": "Missing user_id or xp"}), 400

    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET xp = xp + ? WHERE id = ?", (xp_gained, user_id))
        cursor.execute("SELECT xp FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()

        if not row:
            conn.close()
            return jsonify({"error": "User not found"}), 404

        new_xp = row[0]
        new_level = int(new_xp / 500) + 1
        cursor.execute("UPDATE users SET level = ? WHERE id = ?", (new_level, user_id))
        conn.commit()
        conn.close()
        return jsonify({"new_xp": new_xp, "new_level": new_level})
    except Exception as e:
        print(f"XP update error: {e}")
        return jsonify({"error": "Server error"}), 500

# --- AI ROUTES ---
@app.route('/api/flashcards', methods=['POST'])
def flashcards_route():
    text = request.json.get('text', '').strip()
    lang = request.json.get('lang', 'en')
    if not text:
        return jsonify({"error": "No text provided"}), 400
    return jsonify(generate_flashcards(API_KEY, text, lang))

@app.route('/api/quiz', methods=['POST'])
def quiz_route():
    text = request.json.get('text', '').strip()
    lang = request.json.get('lang', 'en')
    if not text:
        return jsonify({"error": "No text provided"}), 400
    return jsonify(generate_quiz(API_KEY, text, lang))

@app.route('/api/simplify', methods=['POST'])
def simplify_route():
    text = request.json.get('text', '').strip()
    lang = request.json.get('lang', 'en')
    if not text:
        return jsonify({"error": "No text provided"}), 400
    return jsonify(simplify_text(API_KEY, text, lang))

if __name__ == '__main__':
    print("🚀 LearnFast server starting on http://127.0.0.1:5001")
    print(f"📧 Email configured: {'✅' if SENDER_EMAIL else '❌'}")
    print(f"🤖 AI Key configured: {'✅' if API_KEY else '❌'}")
    app.run(host='0.0.0.0', port=5001, debug=True)