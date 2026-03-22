# 🎯 TalentScout AI — Intelligent Hiring Assistant

> An AI-powered conversational chatbot that conducts initial candidate screening interviews through a beautiful, modern Streamlit interface.

---

## ✨ Features

| Feature | Detail |
|---|---|
| **Conversational Flow** | Guided stage-by-stage interview — no form filling |
| **Smart Validation** | Email & phone validated before moving forward |
| **LLM Question Generation** | 5 tailored technical questions generated per candidate |
| **Live Sidebar** | Candidate profile builds in real time as you chat |
| **Progress Tracking** | Visual progress bar + Q&A counter |
| **Dual LLM Support** | Works with OpenAI (GPT) or Anthropic (Claude) |
| **Modern Dark UI** | Glass morphism, gradient animations, chat bubbles |
| **Typing Indicator** | Animated dots while the bot "thinks" |
| **In-Memory + Snapshot** | Candidates saved to JSON automatically |

---

## 📁 Project Structure

```
TalentScout-AI/
│
├── app.py               ← Streamlit UI: layout, chat rendering, sidebar
├── chatbot.py           ← TalentScoutBot: stage machine, LLM calls
├── prompt_engine.py     ← All prompt templates (UI copy + LLM prompts)
├── utils.py             ← Validators, parsers, HTML formatters, stage info
├── data_handler.py      ← In-memory candidate store + JSON snapshot
│
├── assets/
│   └── styles.css       ← Full custom dark UI (glass morphism theme)
│
├── data/
│   └── sample_candidates.json       ← Sample data
│   └── candidates_session.json      ← Auto-generated session snapshot
│
├── config/
│   └── settings.py      ← Settings loader (legacy, kept for compatibility)
│
├── requirements.txt
├── .env                 ← API keys (not committed to git)
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

### 4. Configure API keys
Edit `.env`:
```env
LLM_PROVIDER=openai          # or: anthropic
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-... # only if using Anthropic
MODEL_NAME=gpt-4o-mini
TEMPERATURE=0.7
MAX_TOKENS=1024
```

### 5. Run
```bash
streamlit run app.py
```

Open **http://localhost:8501** in your browser.

---

## 🤖 How It Works

### Conversation Flow

```
Greeting
   │
   ▼
Collect Name → Email → Phone → Experience → Position → Location → Tech Stack
                                                                       │
                                                                       ▼
                                                          LLM generates 5 questions
                                                                       │
                                                                       ▼
                                                          Technical Q&A (5 questions)
                                                                       │
                                                                       ▼
                                                               Closing + Save
```

### Stage Machine

`TalentScoutBot` maintains a `stage` attribute that progresses through a fixed list:

```python
STAGES = [
    "greeting", "collect_name", "collect_email", "collect_phone",
    "collect_experience", "collect_position", "collect_location",
    "collect_tech_stack", "technical_questions", "closing"
]
```

Each user message is routed to the corresponding handler (`_handle_*`). Handlers validate input, store data, advance the stage, and return the next prompt string.

---

## 🧠 Prompt Design

### Philosophy

All prompts live in `prompt_engine.py` — completely separated from business logic. This makes them easy to A/B test, translate, or hand off to a copywriter.

### Three prompt categories

| Category | Purpose | Location |
|---|---|---|
| **UI Prompts** | User-facing messages (greetings, asks, errors) | Static methods in `PromptEngine` |
| **System Prompt** | Sets the LLM's persona and ground rules | `PromptEngine.system_prompt()` |
| **Generation Prompt** | Instructs the LLM to produce interview questions | `PromptEngine.generate_questions_prompt()` |

### Question generation prompt (excerpt)

```
Generate exactly 5 interview questions for a candidate applying for
the role of {position} with {experience} years of experience.
Their tech stack includes: {tech_stack}.

Requirements:
- Questions must be practical and directly relevant to the listed technologies
- Range from beginner-friendly to intermediate level
- Return ONLY a numbered list (1. ... 2. ... etc.), nothing else
```

The `ONLY a numbered list` constraint makes parsing reliable — `chatbot.py` strips leading numbers and filters short lines.

---

## 💾 Data Handling

`DataHandler` provides an in-memory key-value store (`dict`). On every `save_candidate()` call it:

1. Derives a stable candidate ID from the email (MD5 hash, first 12 chars)
2. Writes a full record (profile + answers + timestamp) to `_store`
3. Snapshots the store to `data/candidates_session.json` (fails silently)

To connect a real database, replace `_store` operations with your ORM/driver — the public interface stays the same.

---

## ⚙️ Configuration Reference

| Variable | Default | Description |
|---|---|---|
| `LLM_PROVIDER` | `openai` | `openai` or `anthropic` |
| `OPENAI_API_KEY` | — | Required for OpenAI |
| `ANTHROPIC_API_KEY` | — | Required for Anthropic |
| `MODEL_NAME` | `gpt-4o-mini` | Model ID to use |
| `TEMPERATURE` | `0.7` | LLM creativity (0–1) |
| `MAX_TOKENS` | `1024` | Max response length |

---

## 🛡️ Exit & Fallback Handling

**Exit keywords** (`exit`, `quit`, `bye`, `goodbye`, `stop`, `end`) trigger an immediate polite farewell regardless of stage.

**`help` / `?`** returns a context-aware hint about what to enter at the current stage.

**Unknown / invalid input** returns a generic rephrasing request: *"I didn't quite catch that — could you please rephrase?"*

---

## 📦 Dependencies

```
streamlit    ≥1.33   UI framework
openai       ≥1.30   GPT API client
anthropic    ≥0.25   Claude API client
python-dotenv        .env loading
```

---

*Built with ❤️ using Python, Streamlit, and the OpenAI / Anthropic APIs.*
