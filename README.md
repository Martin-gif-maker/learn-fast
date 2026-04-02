# 🧠 LearnFast

> An AI-powered study platform that turns your notes into flashcards, quizzes, and simplified explanations — built by students, for students.

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python)
![Flask](https://img.shields.io/badge/Flask-Backend-black?style=flat-square&logo=flask)
![Groq](https://img.shields.io/badge/Groq-LLaMA_3.3-orange?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

---

## 🚀 What is LearnFast?

LearnFast is a full-stack web application that uses AI to make studying faster, smarter, and more engaging. Paste any text — a lesson, a chapter, your notes — and the AI instantly generates study tools for you.

Built as a real project by a student who wanted studying to feel less like a chore and more like a game.

---

## ✨ Features

### 🤖 AI-Powered Study Tools
- **Flashcard Generator** — paste your notes, get 5 smart flashcards with questions, answers, and a funny memory hook
- **Quiz Generator** — auto-generates a 5-question multiple choice test with explanations for every answer
- **Smart Study (Text Simplifier)** — explains any complex text simply and clearly, with key takeaways

### 🌍 Bilingual Support (EN / BG)
- Full English and Bulgarian language support across every page
- Language preference saved automatically between sessions

### 🎮 XP & Level System
- Earn XP for every correct quiz answer
- Level up as you study more
- Visual XP progress bar on your dashboard

### 🔐 User Authentication
- Secure registration with email verification (6-digit code)
- Passwords stored with SHA-256 hashing
- Session-based login system

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python, Flask, Flask-CORS |
| Frontend | HTML5, CSS3, Vanilla JavaScript |
| Database | SQLite |
| AI | Groq API (LLaMA 3.3 70B) |
| Auth | Email verification + SHA-256 hashing |
| Config | python-dotenv |

---

## 📁 Project Structure

```
LearnFast/
│
├── ai_models/
│   ├── __init__.py
│   └── ai_brain.py          # All AI logic (flashcards, quiz, simplify)
│
├── First_page.html           # Landing page
├── Log_in_page.html          # Login
├── Sign-in-Page.html         # Registration
├── Main-Page.html            # Dashboard
├── Flash_cards.html          # Flashcard generator
├── Test_subject.html         # Quiz generator
├── text.html                 # Text simplifier
├── Info_page.html            # About us
├── Chose_us_page.html        # Why choose us
│
├── sigma.css                 # Global styles
├── server.py                 # Flask server + API routes
├── requirements.txt
├── .env                      # Secret keys (not on GitHub)
└── .gitignore
```

---

## ⚙️ Setup & Installation

### 1. Clone the repository
```bash
git clone https://github.com/Martin-gif-maker/learnfast.git
cd learnfast
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Create your `.env` file
Create a file called `.env` in the project root:
```
GROQ_API_KEY=your_groq_api_key_here
SENDER_EMAIL=your_email@gmail.com
SENDER_PASSWORD=your_gmail_app_password
SECRET_KEY=any_long_random_string
```

> Get a free Groq API key at [console.groq.com](https://console.groq.com)

### 4. Run the server
```bash
python server.py
```

### 5. Open in browser
```
http://127.0.0.1:5001
```

---

## 🔑 Environment Variables

| Variable | Description |
|----------|-------------|
| `GROQ_API_KEY` | Your Groq API key (free at console.groq.com) |
| `SENDER_EMAIL` | Gmail address used to send verification codes |
| `SENDER_PASSWORD` | Gmail App Password (not your regular password) |
| `SECRET_KEY` | Any random string used for Flask sessions |

---

## 📸 Pages Overview

| Page | Description |
|------|-------------|
| Landing Page | Introduction with 3 entry points |
| Login / Register | Secure auth with email verification |
| Dashboard | XP bar, level, and navigation to tools |
| Flashcards | AI flashcard generator |
| Quiz | AI multiple choice test generator |
| Smart Study | AI text simplifier with key points |
| Info / Why Us | About the project and team |

---

## 🔒 Security

- Passwords are hashed with SHA-256 before storing
- API keys and credentials stored in `.env` (never committed to GitHub)
- Server-side input validation on all API routes
- `.gitignore` excludes `.env` and the database file

---

## 🗺️ Roadmap

- [ ] Streak tracking system
- [ ] Spaced repetition for flashcards
- [ ] Leaderboard between users
- [ ] Mobile-responsive redesign
- [ ] Deploy to cloud (Render / Railway)

---

## 👨‍💻 Author

**Martin** — [@Martin-gif-maker](https://github.com/Martin-gif-maker)

Built as a personal project to make studying smarter and more engaging.

---

## 📄 License

This project is open source under the [MIT License](LICENSE).