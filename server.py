"""LearnFast -- Flask application entrypoint.

Routes
------
GET  /                   Landing page
GET  /<filename>         Serve static HTML/CSS/JS

POST /api/send-code      Send email verification code
POST /api/register       Register new user
POST /api/login          Log in
POST /api/logout         Log out
POST /api/update-xp      Add XP, recalculate level

POST /api/flashcards     Generate flashcards (AI)
POST /api/quiz           Generate quiz (AI)
POST /api/simplify       Simplify text (AI)
"""
from __future__ import annotations

import logging
import random
import smtplib
import sqlite3
from contextlib import contextmanager
from email.message import EmailMessage
from typing import Iterator

import bcrypt
from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory, session
from flask_cors import CORS

from ai_models.ai_brain import generate_flashcards, generate_quiz, simplify_text
from config import settings

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

load_dotenv()

# ---------------------------------------------------------------------------
# Flask app
# ---------------------------------------------------------------------------
app = Flask(__name__)
app.secret_key = settings.secret_key
CORS(app, supports_credentials=True)


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------
@contextmanager
def db_cursor() -> Iterator[sqlite3.Cursor]:
    """Open a DB connection, yield a cursor, commit, and always close."""
    conn = sqlite3.connect(settings.db_path)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.cursor()
        yield cur
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    """Create the users table if it does not already exist."""
    with db_cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                name     TEXT NOT NULL,
                email    TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                xp       INTEGER DEFAULT 0,
                level    INTEGER DEFAULT 1
            )
        """)
    logger.info("Database initialised at %s", settings.db_path)


# ---------------------------------------------------------------------------
# Password hashing (bcrypt -- secure, salted)
# ---------------------------------------------------------------------------
def hash_password(plain: str) -> str:
    """Return a bcrypt hash of plain."""
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Return True if plain matches the stored bcrypt hash."""
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Email verification
# NOTE: codes stored in-process -- use Redis in multi-worker production.
# ---------------------------------------------------------------------------
_pending_codes: dict[str, str] = {}


def send_verification_email(to_email: str, code: str) -> bool:
    """Email a 6-digit code. Prints to console if email is not configured."""
    if not settings.sender_email or not settings.sender_password:
        logger.warning("Email not configured -- code for %s: %s", to_email, code)
        return True
    msg = EmailMessage()
    msg["Subject"] = "LearnFast -- Your Verification Code"
    msg["From"] = settings.sender_email
    msg["To"] = to_email
    msg.set_content(f"Your LearnFast code: {code}\n\nExpires in 10 minutes.")
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as srv:
            srv.login(settings.sender_email, settings.sender_password)
            srv.send_message(msg)
        logger.info("Verification email sent to %s", to_email)
        return True
    except Exception:
        logger.exception("Email failed for %s -- code: %s", to_email, code)
        return False


# ---------------------------------------------------------------------------
# Static routes
# ---------------------------------------------------------------------------
@app.route("/")
def home():
    """Serve the landing page."""
    return send_from_directory(".", "First_page.html")


@app.route("/<path:filename>")
def serve_static(filename: str):
    """Serve any static file from the project root."""
    return send_from_directory(".", filename)


# ---------------------------------------------------------------------------
# Auth routes
# ---------------------------------------------------------------------------
@app.route("/api/send-code", methods=["POST"])
def send_verification_code():
    """Send a 6-digit email verification code."""
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip().lower()
    if not email:
        return jsonify({"error": "Email is required."}), 400
    with db_cursor() as cur:
        cur.execute("SELECT id FROM users WHERE email = ?", (email,))
        if cur.fetchone():
            return jsonify({"error": "Email already registered."}), 400
    code = str(random.randint(100_000, 999_999))
    _pending_codes[email] = code
    send_verification_email(email, code)
    return jsonify({"message": "Verification code sent."})


@app.route("/api/register", methods=["POST"])
def register():
    """Create a new user account after email verification.

    Expects JSON: {email, name, password, code}.
    """
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip().lower()
    name = data.get("name", "").strip()
    password = data.get("password", "")
    code = data.get("code", "")

    if not all([email, name, password, code]):
        return jsonify({"error": "All fields are required."}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters."}), 400
    if _pending_codes.get(email) != code:
        return jsonify({"error": "Invalid or expired verification code."}), 400

    try:
        with db_cursor() as cur:
            cur.execute(
                "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                (name, email, hash_password(password)),
            )
        _pending_codes.pop(email, None)
        logger.info("New user registered: %s", email)
        return jsonify({"message": "Account created successfully."})
    except sqlite3.IntegrityError:
        return jsonify({"error": "Email already registered."}), 400
    except Exception:
        logger.exception("Registration error for %s", email)
        return jsonify({"error": "Server error during registration."}), 500


@app.route("/api/login", methods=["POST"])
def login():
    """Validate credentials and start a session.

    Expects JSON: {email, password}.
    """
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"error": "Email and password are required."}), 400

    with db_cursor() as cur:
        cur.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cur.fetchone()

    if not user or not verify_password(password, user["password"]):
        return jsonify({"error": "Invalid email or password."}), 401

    session["user_id"] = user["id"]
    logger.info("User logged in: %s (id=%d)", email, user["id"])
    return jsonify({
        "message": "Login successful.",
        "user": {"id": user["id"], "name": user["name"], "xp": user["xp"], "level": user["level"]},
    })


@app.route("/api/logout", methods=["POST"])
def logout():
    """Clear the session."""
    session.clear()
    return jsonify({"message": "Logged out."})


@app.route("/api/update-xp", methods=["POST"])
def update_xp():
    """Add XP to a user and recalculate level (level = xp // 500 + 1).

    Expects JSON: {user_id, xp}.
    """
    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id")
    xp_gained = data.get("xp")

    if user_id is None or xp_gained is None:
        return jsonify({"error": "Missing user_id or xp."}), 400

    try:
        with db_cursor() as cur:
            cur.execute("UPDATE users SET xp = xp + ? WHERE id = ?", (xp_gained, user_id))
            cur.execute("SELECT xp FROM users WHERE id = ?", (user_id,))
            row = cur.fetchone()
            if not row:
                return jsonify({"error": "User not found."}), 404
            new_xp = row["xp"]
            new_level = int(new_xp / 500) + 1
            cur.execute("UPDATE users SET level = ? WHERE id = ?", (new_level, user_id))
        logger.info("XP updated: user=%s +%s => total=%d level=%d", user_id, xp_gained, new_xp, new_level)
        return jsonify({"new_xp": new_xp, "new_level": new_level})
    except Exception:
        logger.exception("XP update failed for user=%s", user_id)
        return jsonify({"error": "Server error."}), 500


# ---------------------------------------------------------------------------
# AI routes
# ---------------------------------------------------------------------------
@app.route("/api/flashcards", methods=["POST"])
def flashcards_route():
    """Generate 5 flashcards from study text.

    Expects JSON: {text, lang} where lang is 'en' or 'bg'.
    """
    data = request.get_json(silent=True) or {}
    text = data.get("text", "").strip()
    lang = data.get("lang", "en")
    if not text:
        return jsonify({"error": "No text provided."}), 400
    logger.info("Generating flashcards (lang=%s, chars=%d)", lang, len(text))
    return jsonify(generate_flashcards(text, lang))


@app.route("/api/quiz", methods=["POST"])
def quiz_route():
    """Generate a 5-question multiple-choice quiz from study text.

    Expects JSON: {text, lang} where lang is 'en' or 'bg'.
    """
    data = request.get_json(silent=True) or {}
    text = data.get("text", "").strip()
    lang = data.get("lang", "en")
    if not text:
        return jsonify({"error": "No text provided."}), 400
    logger.info("Generating quiz (lang=%s, chars=%d)", lang, len(text))
    return jsonify(generate_quiz(text, lang))


@app.route("/api/simplify", methods=["POST"])
def simplify_route():
    """Simplify study text to beginner level.

    Expects JSON: {text, lang} where lang is 'en' or 'bg'.
    """
    data = request.get_json(silent=True) or {}
    text = data.get("text", "").strip()
    lang = data.get("lang", "en")
    if not text:
        return jsonify({"error": "No text provided."}), 400
    logger.info("Simplifying text (lang=%s, chars=%d)", lang, len(text))
    return jsonify(simplify_text(text, lang))


# ---------------------------------------------------------------------------
# Startup + local dev runner
# ---------------------------------------------------------------------------
init_db()

if __name__ == "__main__":
    logger.info("LearnFast starting on http://%s:%d", settings.host, settings.port)
    logger.info(
        "Email configured: %s",
        "yes" if settings.sender_email else "no (codes will print to console)",
    )
    app.run(host=settings.host, port=settings.port, debug=settings.debug)
