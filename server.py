import os
import sys
import sqlite3
import random
import smtplib
from email.message import EmailMessage
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# --- PATH SETUP ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AI_FOLDER = os.path.join(BASE_DIR, 'ai_models')
sys.path.append(AI_FOLDER)

# Try to import your AI brain
try:
    from ai_brain import generate_flashcards, generate_quiz, simplify_text
except ImportError:
    try:
        from ai_models.ai_brain import generate_flashcards, generate_quiz, simplify_text
    except ImportError:
        print("⚠️ WARNING: Could not find 'ai_brain.py'. AI features might fail.")
        # Dummy functions to prevent server crash if file is missing
        def generate_flashcards(k, t, l): return {"flashcards": []}
        def generate_quiz(k, t, l): return {"quiz": []}
        def simplify_text(k, t, l): return {"simplified_content": "AI Error", "key_points": []}

app = Flask(__name__)
CORS(app) # Allows browser to talk to server easily

# --- CONFIG ---
API_KEY = "AIzaSyAvwquAuou9BSnNhuHq3BVmVeQkPvJqjXI"
DB_FILE = os.path.join(BASE_DIR, "learnfast.db")
SENDER_EMAIL = "learnfast86@gmail.com"
SENDER_PASSWORD = "wyix eiyl tioq xjtp"

verification_codes = {}

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

def send_code_via_email(to_email, code):
    msg = EmailMessage()
    msg['Subject'] = "🚀 Launch Codes: Learn Fast"
    msg['From'] = SENDER_EMAIL
    msg['To'] = to_email
    msg.set_content(f"Your verification code is: {code}")

    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"❌ Email Error: {e}")
        return False

# --- WEB ROUTES (FRONTEND) ---
@app.route('/')
def home():
    return send_from_directory(BASE_DIR, 'First_page.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory(BASE_DIR, filename)

# --- API ROUTES (BACKEND) ---
@app.route('/api/send-code', methods=['POST'])
def send_verification_code():
    data = request.json
    email = data.get('email')
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    if cursor.fetchone():
        conn.close()
        return jsonify({"error": "Email already registered!"}), 400
    conn.close()

    code = str(random.randint(100000, 999999))
    verification_codes[email] = code

    if send_code_via_email(email, code):
        return jsonify({"message": "Code sent"})
    else:
        # For testing, if email fails, print code to terminal so you can still log in
        print(f"⚠️ Email failed. CODE FOR {email}: {code}")
        return jsonify({"message": "Email failed (Check Terminal for Code)"})

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    # Check code
    if data['email'] not in verification_codes or verification_codes[data['email']] != data['code']:
        return jsonify({"error": "Invalid Code!"}), 400

    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                       (data['name'], data['email'], data['password']))
        conn.commit()
        conn.close()
        del verification_codes[data['email']]
        return jsonify({"message": "Success"})
    except:
        return jsonify({"error": "DB Error"}), 500

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ? AND password = ?", (data['email'], data['password']))
    user = cursor.fetchone()
    conn.close()
    if user:
        return jsonify({"message": "Success", "user": {"id": user[0], "name": user[1], "xp": user[4], "level": user[5]}})
    return jsonify({"error": "Invalid credentials"}), 401

@app.route('/api/update-xp', methods=['POST'])
def update_xp():
    data = request.json
    user_id = data.get('user_id')
    xp_gained = data.get('xp')
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET xp = xp + ? WHERE id = ?", (xp_gained, user_id))
    cursor.execute("SELECT xp FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    if row:
        new_xp = row[0]
        new_level = int(new_xp / 500) + 1
        cursor.execute("UPDATE users SET level = ? WHERE id = ?", (new_level, user_id))
        conn.commit()
        conn.close()
        return jsonify({"new_xp": new_xp, "new_level": new_level})
    return jsonify({"error": "User not found"}), 404

@app.route('/api/flashcards', methods=['POST'])
def flashcards_route():
    return jsonify(generate_flashcards(API_KEY, request.json.get('text', ''), request.json.get('lang', 'en')))

@app.route('/api/quiz', methods=['POST'])
def quiz_route():
    return jsonify(generate_quiz(API_KEY, request.json.get('text', ''), request.json.get('lang', 'en')))

@app.route('/api/simplify', methods=['POST'])
def simplify_route():
    return jsonify(simplify_text(API_KEY, request.json.get('text', ''), request.json.get('lang', 'en')))

if __name__ == '__main__':
    # Force Port 5001 for Mac compatibility
    print("🚀 Server starting on http://127.0.0.1:5001")
    app.run(host='0.0.0.0', port=5001, debug=True)