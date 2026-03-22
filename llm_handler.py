"""
llm_handler.py
══════════════
Groq API integration for TalentScout AI — Hybrid Model Architecture.

Model strategy
──────────────
  FAST_MODEL  (llama3-8b-8192)          — chat / conversation responses
      • Low latency, sufficient for greetings, follow-ups, acknowledgements
      • Keeps the interview feel snappy

  SMART_MODEL (llama-3.3-70b-versatile) — technical question generation
      • Higher reasoning quality for domain-specific interview questions
      • Called once per interview; result is cached per tech stack

Performance optimisations
─────────────────────────
  1. Two-model routing  — only escalate to the powerful model when needed
  2. Question caching   — same tech+role+experience combo is generated once
  3. History trimming   — only the last MAX_HISTORY_TURNS are sent to the API,
                          capping token usage without losing conversational flow

Public API
──────────
  generate_response(conversation_history, system_prompt) → str
  generate_tech_questions(tech_stack, position, experience) → list[str]
"""

import os
import re
import hashlib
import logging

from dotenv import load_dotenv
from groq import Groq

# Always win over a stale os.environ (handles .env edits without restart)
load_dotenv(override=True)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

def _env(key: str, default: str) -> str:
    """Read an env var and strip any accidental surrounding quotes / spaces."""
    return os.getenv(key, default).strip().strip('"').strip("'").strip()


# ── Model identifiers (overridable via .env) ──────────────────────────────────
FAST_MODEL  = _env("GROQ_FAST_MODEL",  "llama-3.1-8b-instant")     # ⚡ chat
SMART_MODEL = _env("GROQ_SMART_MODEL", "llama-3.3-70b-versatile")  # 🧠 questions

# ── Sampling parameters ───────────────────────────────────────────────────────
TEMPERATURE       = float(_env("TEMPERATURE", "0.7"))
MAX_TOKENS_CHAT   = int(_env("MAX_TOKENS", "512"))
MAX_TOKENS_QUEST  = 1024    # generous budget for a numbered question list

# ── History window ────────────────────────────────────────────────────────────
# Only the most recent N user+assistant *pairs* are sent to the API.
# This prevents token bloat in long interviews while keeping context fresh.
MAX_HISTORY_TURNS = int(_env("MAX_HISTORY_TURNS", "5"))

# ── Fallback questions (used when the API is unreachable) ─────────────────────
_FALLBACK_QUESTIONS = [
    "Explain the core concepts of your primary technology and how you apply them day-to-day.",
    "Describe a technically challenging problem you solved recently. Walk us through your approach.",
    "How do you ensure code quality and maintainability in your projects?",
    "How do you approach debugging a complex issue in a production environment?",
    "How do you stay current with emerging tools and best practices in your field?",
]

_ERROR_RESPONSE = "Sorry, something went wrong on my end. Could you please try again?"

# ── Question cache ────────────────────────────────────────────────────────────
# Maps a deterministic hash of (tech_stack, position, experience) → question list.
# Survives for the lifetime of the Python process (i.e. one Streamlit session).
_question_cache: dict[str, list[str]] = {}


# ═══════════════════════════════════════════════════════════════════════════════
# INTERNAL HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def _get_client() -> Groq:
    """
    Build a Groq client using the API key read fresh from the environment.
    Called on every outbound request — no caching — so a key change in .env
    takes effect on the next message without restarting the app.
    """
    load_dotenv(override=True)
    api_key = _env("GROQ_API_KEY", "")
    if not api_key:
        raise EnvironmentError(
            "GROQ_API_KEY is not set. "
            "Add it to your .env file:  GROQ_API_KEY=gsk_..."
        )
    return Groq(api_key=api_key)


def _trim_history(history: list[dict]) -> list[dict]:
    """
    Return the tail of the conversation history capped at MAX_HISTORY_TURNS
    user+assistant pairs.

    Sending only recent context:
      • Reduces token usage on every chat call
      • Keeps the fast model's context window from overflowing
      • The system prompt always carries the full candidate profile,
        so no critical information is lost
    """
    max_messages = MAX_HISTORY_TURNS * 2   # each turn = 1 user + 1 assistant
    if len(history) <= max_messages:
        return history
    trimmed = history[-max_messages:]
    logger.debug("History trimmed: %d → %d messages", len(history), len(trimmed))
    return trimmed


def _question_cache_key(tech_stack: list[str], position: str, experience: str) -> str:
    """
    Build a stable, order-independent cache key for a question-generation
    request.  Sorting the tech list ensures ["Python","React"] and
    ["React","Python"] produce the same key.
    """
    normalised = sorted(t.lower().strip() for t in tech_stack)
    raw        = "|".join(normalised) + f"|{position.lower().strip()}|{experience.lower().strip()}"
    return hashlib.md5(raw.encode()).hexdigest()


def _parse_numbered_list(raw: str) -> list[str]:
    """
    Extract question strings from LLM output like:
      1. What is ...
      2) How would you ...
    Returns at most 5 items; skips blank lines and short header artefacts.
    """
    questions = []
    for line in raw.splitlines():
        line    = line.strip()
        cleaned = re.sub(r"^\d+[\.\)\:]?\s*", "", line).strip()
        if len(cleaned) > 15:
            questions.append(cleaned)
    return questions[:5]


# ═══════════════════════════════════════════════════════════════════════════════
# PUBLIC API
# ═══════════════════════════════════════════════════════════════════════════════

def generate_response(
    conversation_history: list[dict],
    system_prompt: str,
    temperature: float = TEMPERATURE,
    max_tokens: int    = MAX_TOKENS_CHAT,
) -> str:
    """
    Generate a conversational reply using the FAST model (llama3-8b-8192).

    Used for:  greetings · info collection · acknowledgements · fallbacks ·
               question delivery · closing

    The conversation history is automatically trimmed to the last
    MAX_HISTORY_TURNS pairs before being sent to the API.

    Parameters
    ----------
    conversation_history : list[{"role": "user"|"assistant", "content": str}]
        Do NOT include the system message — injected automatically.
    system_prompt : str
        Persona + stage-specific task instruction.
    temperature : float
        0 = deterministic, 1 = creative.  Defaults to TEMPERATURE env var.
    max_tokens : int
        Upper bound on reply length.  Defaults to MAX_TOKENS env var.

    Returns
    -------
    str  — model reply, or a friendly error string on failure.
    """
    trimmed  = _trim_history(conversation_history)
    messages = [{"role": "system", "content": system_prompt}] + trimmed

    try:
        client   = _get_client()
        response = client.chat.completions.create(
            model       = FAST_MODEL,
            messages    = messages,
            temperature = temperature,
            max_tokens  = max_tokens,
        )
        reply = response.choices[0].message.content.strip()
        logger.debug("[FAST %s] reply (%d chars): %s…", FAST_MODEL, len(reply), reply[:80])
        return reply

    except EnvironmentError as exc:
        logger.error("Config error: %s", exc)
        return (
            "⚠️ **API key not configured.** "
            "Please add your `GROQ_API_KEY` to the `.env` file and restart the app."
        )
    except Exception as exc:
        logger.error("[FAST] Groq API error: %s", exc)
        return _ERROR_RESPONSE


def generate_tech_questions(
    tech_stack: list[str],
    position:   str = "",
    experience: str = "",
) -> list[str]:
    """
    Generate 5 tailored technical interview questions using the SMART model
    (llama-3.3-70b-versatile).

    Results are **cached** — if the same tech stack + role + experience
    combination is requested again (e.g. after a page refresh), the cached
    list is returned immediately without a second API call.

    Parameters
    ----------
    tech_stack  : list of technology names (e.g. ["Python", "React", "PostgreSQL"])
    position    : job title the candidate is applying for
    experience  : years of experience as a string (e.g. "3 years")

    Returns
    -------
    list[str]   — exactly 5 question strings.
                  Falls back to generic questions on API failure.
    """
    if not tech_stack:
        return _FALLBACK_QUESTIONS

    # ── Cache hit ─────────────────────────────────────────────────────────────
    cache_key = _question_cache_key(tech_stack, position, experience)
    if cache_key in _question_cache:
        logger.debug("[SMART] Cache hit for key %s", cache_key[:8])
        return _question_cache[cache_key]

    # ── Build prompt ──────────────────────────────────────────────────────────
    techs       = ", ".join(tech_stack)
    role_clause = f"the role of **{position}**" if position else "a software engineering role"
    exp_clause  = f"with **{experience}** of professional experience" if experience else ""

    prompt = (
        "You are a senior technical interviewer conducting an initial screening.\n\n"
        f"Generate exactly 5 technical interview questions for a candidate applying for "
        f"{role_clause} {exp_clause}.\n\n"
        f"Their tech stack includes: {techs}\n\n"
        "Rules:\n"
        "- Each question must directly reference one or more of the listed technologies\n"
        "- Questions 1–2: beginner-friendly (concepts, definitions, basic usage)\n"
        "- Questions 3–5: intermediate (design decisions, debugging, trade-offs)\n"
        "- Open-ended and practical — not trivia or yes/no\n"
        "- Return ONLY a numbered list, no preamble, no answers:\n"
        "  1. ...\n"
        "  2. ...\n"
        "  3. ...\n"
        "  4. ...\n"
        "  5. ..."
    )

    try:
        client   = _get_client()
        response = client.chat.completions.create(
            model       = SMART_MODEL,
            messages    = [{"role": "user", "content": prompt}],
            temperature = 0.75,          # slightly higher for creative questions
            max_tokens  = MAX_TOKENS_QUEST,
        )
        raw       = response.choices[0].message.content.strip()
        questions = _parse_numbered_list(raw)
        result    = questions if len(questions) >= 3 else _FALLBACK_QUESTIONS

        logger.debug(
            "[SMART %s] Generated %d questions for: %s",
            SMART_MODEL, len(result), techs[:60]
        )

        # ── Store in cache ────────────────────────────────────────────────────
        _question_cache[cache_key] = result
        return result

    except Exception as exc:
        logger.error("[SMART] Question generation failed: %s", exc)
        return _FALLBACK_QUESTIONS


# ── Utility (exposed for tests / debugging) ───────────────────────────────────

def get_model_info() -> dict:
    """Return the active model configuration for display in the UI or logs."""
    return {
        "fast_model":        FAST_MODEL,
        "smart_model":       SMART_MODEL,
        "temperature":       TEMPERATURE,
        "max_tokens_chat":   MAX_TOKENS_CHAT,
        "max_tokens_quest":  MAX_TOKENS_QUEST,
        "max_history_turns": MAX_HISTORY_TURNS,
        "cached_question_sets": len(_question_cache),
    }
