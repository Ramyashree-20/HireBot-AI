# 🎯 TalentScout AI — Intelligent Hiring Assistant

> An AI-powered technical screening assistant that collects candidate details through a profile form, then conducts a personalised technical interview using dynamically generated questions — all inside a sleek dark Streamlit interface.

---

## ✨ Features

| Feature | Detail |
|---|---|
| **Two-page flow** | Profile form → AI chat interview → Closing page |
| **Hybrid LLM architecture** | Fast model for chat, smart model for question generation |
| **Dynamic question generation** | 5 tailored technical questions generated per candidate from their exact tech stack |
| **Question caching** | Same tech stack + role + experience combo is generated only once per session |
| **History trimming** | Only last 5 conversation turns sent to the API — prevents token bloat |
| **Smart validation** | Email, phone, name and tech stack validated before submission |
| **Live sidebar** | Full candidate profile + Q&A progress bar visible throughout the interview |
| **Closing page** | Dedicated completion screen shown after all questions are answered |
| **Modern dark UI** | Glass morphism, gradient animations, chat bubbles, typing indicator |
| **Candidate snapshots** | Interview data auto-saved to JSON per session |

---

## 📁 Project Structure

```
TalentScout-AI/
│
├── app.py               ← Streamlit entry point: two-page router, form, chat, closing page
├── chatbot.py           ← TalentScoutBot: stage machine + hybrid LLM routing
├── llm_handler.py       ← Groq API integration: fast model (chat) + smart model (questions)
├── prompt_engine.py     ← All system prompts and task strings per stage
├── utils.py             ← Validators, parsers, HTML formatters
├── data_handler.py      ← In-memory candidate store + JSON snapshot
│
├── assets/
│   └── styles.css       ← Full custom dark UI (glass morphism theme)
│
├── .streamlit/
│   └── config.toml      ← Streamlit server config (headless, CORS off — for Render)
│
├── data/
│   └── candidates_session.json   ← Auto-generated at runtime (git-ignored)
│
├── render.yaml          ← Render.com deployment blueprint
├── requirements.txt
├── .env                 ← API keys (never committed — see .gitignore)
├── .gitignore
└── README.md
```

---

## 🚀 Quick Start

### 1. Clone the repository
```bash
git clone https://github.com/your-username/TalentScout-AI.git
cd TalentScout-AI
```

### 2. Create a virtual environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure your API key

Create a `.env` file in the project root:

```env
# Required
GROQ_API_KEY=gsk_...your_key_here...

# Models (defaults shown — override if needed)
GROQ_FAST_MODEL=llama-3.1-8b-instant
GROQ_SMART_MODEL=llama-3.3-70b-versatile

# Sampling
TEMPERATURE=0.7
MAX_TOKENS=512

# History window (turns sent to API)
MAX_HISTORY_TURNS=5
```

Get a free Groq API key at [console.groq.com](https://console.groq.com).

### 5. Run
```bash
streamlit run app.py
```

Open **http://localhost:8501** in your browser.

---

## 🤖 How It Works

### Application Flow

```
┌─────────────────────────────┐
│   Page 1 — Profile Form     │
│                             │
│  Name, Email, Phone         │
│  Experience, Position       │
│  Location, Tech Stack       │
│                             │
│  [🚀 Start My Interview]    │
└────────────┬────────────────┘
             │  Form submitted
             ▼
  Smart model generates 5
  tailored technical questions
  (cached per stack+role+exp)
             │
             ▼
┌─────────────────────────────┐
│   Page 2 — AI Chat          │
│                             │
│  Bot greets candidate by    │
│  name and asks Question 1   │
│                             │
│  Candidate answers each     │
│  question in the chat box   │
│                             │
│  Progress bar in sidebar    │
└────────────┬────────────────┘
             │  All 5 answered
             ▼
┌─────────────────────────────┐
│   Closing Page              │
│                             │
│  🎉 Interview Complete!     │
│  Personalised closing msg   │
│  Expected response time     │
│  [🔄 Start New Interview]   │
└─────────────────────────────┘
```

### Hybrid LLM Architecture

Two Groq models are used, routed transparently by `llm_handler.py`:

| Model | Role | When called |
|---|---|---|
| `llama-3.1-8b-instant` ⚡ | **Fast model** — all conversational responses | Every chat turn |
| `llama-3.3-70b-versatile` 🧠 | **Smart model** — technical question generation | Once per interview (result cached) |

This keeps the interview feeling snappy while ensuring high-quality, domain-specific questions.

### Stage Machine

`TalentScoutBot` drives the interview through a fixed sequence of stages:

```python
STAGES = [
    "greeting", "collect_name", "collect_email", "collect_phone",
    "collect_experience", "collect_position", "collect_location",
    "collect_tech_stack", "technical_questions", "closing"
]
```

When using the **profile form** (Page 1), the bot skips directly to `technical_questions` via `initialize_with_form_data()` — all info-collection stages are bypassed.

---

## 🧠 Prompt Design

All prompts live in `prompt_engine.py`, fully separated from business logic.

### System prompt structure

Every API call receives a system prompt built from three layers:

```
[Persona]
You are TalentScout AI, a professional and friendly hiring assistant...

[Candidate Profile]
Name: Jane Doe | Position: Backend Engineer | Experience: 3 years
Tech Stack: Python, FastAPI, PostgreSQL, Docker

[Stage Task]
Present Question 3 of 5: "How would you handle database migrations..."
```

### Question generation prompt

The smart model receives a structured prompt with:
- Candidate's exact tech stack
- Target role and experience level
- Rules: Q1–Q2 beginner, Q3–Q5 intermediate, open-ended, no trivia

Output is parsed via regex (`_parse_numbered_list`) and cached by MD5 key of `sorted(techs)|position|experience`.

---

## 💾 Data Handling

`DataHandler` stores candidate records in memory during the session and snapshots to `data/candidates_session.json` after every save.

Each record contains:
- Full candidate profile (name, email, phone, experience, position, location, tech stack)
- All Q&A pairs (question + candidate's answer)
- Timestamp

Candidate ID is derived from MD5 of their email — ensures idempotent saves on repeat submissions.

---

## ⚙️ Configuration Reference

| Variable | Default | Description |
|---|---|---|
| `GROQ_API_KEY` | — | **Required.** Your Groq API key |
| `GROQ_FAST_MODEL` | `llama-3.1-8b-instant` | Model used for all chat responses |
| `GROQ_SMART_MODEL` | `llama-3.3-70b-versatile` | Model used for question generation |
| `TEMPERATURE` | `0.7` | LLM creativity (0 = deterministic, 1 = creative) |
| `MAX_TOKENS` | `512` | Max tokens per chat response |
| `MAX_HISTORY_TURNS` | `5` | Conversation turns sent to API (controls token usage) |

---

## 🛡️ Validation & Fallbacks

**Form validation** (Page 1) — all fields checked before submission:
- Name: at least 2 characters with a letter
- Email: RFC-style regex (`user@domain.tld`)
- Phone: 7–15 digits, optional country code and separators
- Tech stack: at least one parseable technology

**Chat fallbacks:**
- Exit keywords (`exit`, `quit`, `bye`, `goodbye`, `stop`, `end`) → immediate polite farewell
- `help` / `?` → context-aware hint for current stage
- Empty input → rephrasing request without advancing stage

**API fallbacks** — if Groq is unreachable, `generate_tech_questions()` returns 5 generic questions so the interview still runs.

---

## 🌐 Deploy to Render

The project ships with `render.yaml` for one-click deployment.

### Steps

1. Push this repo to GitHub
2. Go to [render.com](https://render.com) → **New → Web Service** → connect your repo
3. Render auto-detects `render.yaml` — click **Apply**
4. In the Render dashboard → **Environment** tab, add:
   ```
   GROQ_API_KEY = gsk_...your_key...
   ```
   (All other env vars are pre-set in `render.yaml`)
5. Click **Deploy**

Your app will be live at `https://talentscout-ai.onrender.com`.

> **Note:** The free Render tier spins down after 15 min of inactivity. The first request after that takes ~30 s to wake up.

---

## 📦 Dependencies

```
streamlit    ≥1.33    UI framework
groq         ≥0.9     Groq API client (Llama 3 inference)
python-dotenv         .env loading
```

---

*Built with ❤️ using Python, Streamlit, and the Groq API (Llama 3).*
