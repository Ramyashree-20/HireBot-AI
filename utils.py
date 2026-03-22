"""
utils.py
════════
Shared utility functions: validation, parsing, formatting, and UI helpers.
"""

import re
import html


# ── Validators ────────────────────────────────────────────────────────────────

def validate_email(email: str) -> bool:
    """Return True if email matches a standard pattern."""
    pattern = r"^[\w\.\+\-]+@[\w\-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email.strip()))


def validate_phone(phone: str) -> bool:
    """
    Return True if phone contains 7–15 digits (after stripping formatting).
    Accepts: +1 555 000 1234 / (555)000-1234 / 07911123456
    """
    digits = re.sub(r"[\s\-\(\)\+\.]", "", phone)
    return digits.isdigit() and 7 <= len(digits) <= 15


# ── Tech Stack Parser ─────────────────────────────────────────────────────────

def parse_tech_stack(raw: str) -> list[str]:
    """
    Convert a free-form tech stack string into a deduplicated list.
    Splits on commas, slashes, semicolons, and 'and'.
    """
    tokens = re.split(r"[,;/\n]|\band\b", raw, flags=re.IGNORECASE)
    techs = []
    seen = set()
    for t in tokens:
        t = t.strip().strip("•-*").strip()
        if t and t.lower() not in seen:
            seen.add(t.lower())
            techs.append(t)
    return techs


# ── Stage Progress ────────────────────────────────────────────────────────────

_STAGE_META = {
    "greeting":            {"label": "Welcome",              "pct": 0},
    "collect_name":        {"label": "Collecting Info",      "pct": 10},
    "collect_email":       {"label": "Collecting Info",      "pct": 20},
    "collect_phone":       {"label": "Collecting Info",      "pct": 30},
    "collect_experience":  {"label": "Collecting Info",      "pct": 40},
    "collect_position":    {"label": "Collecting Info",      "pct": 50},
    "collect_location":    {"label": "Collecting Info",      "pct": 58},
    "collect_tech_stack":  {"label": "Tech Stack",           "pct": 65},
    "technical_questions": {"label": "Technical Assessment", "pct": 80},
    "closing":             {"label": "Complete ✓",           "pct": 100},
}


def get_stage_info(stage: str) -> dict:
    """Return display label and progress percentage for the given stage."""
    return _STAGE_META.get(stage, {"label": stage.replace("_", " ").title(), "pct": 0})


# ── HTML Formatters ───────────────────────────────────────────────────────────

def format_message_html(content: str, is_bot: bool = False) -> str:
    """
    Safely convert plain text / light markdown to HTML for chat bubbles.
    Escapes user content to prevent XSS; applies basic markdown to bot content.
    """
    safe = html.escape(content)
    safe = safe.replace("\n", "<br>")
    if is_bot:
        safe = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", safe)
        safe = re.sub(r"\*(.+?)\*",     r"<em>\1</em>",         safe)
        safe = re.sub(r"`(.+?)`",       r"<code style='background:rgba(99,102,241,0.18);border-radius:4px;padding:1px 5px;font-family:monospace;'>\1</code>", safe)
    return safe


def format_tech_tags(tech_list: list[str]) -> str:
    """Render a list of tech names as styled HTML tags."""
    tags = [
        f'<span class="tech-tag">{html.escape(t)}</span>'
        for t in tech_list
    ]
    return " ".join(tags)


def format_candidate_summary(info: dict) -> str:
    """Return a plain-text summary of the collected candidate info."""
    lines = []
    field_map = [
        ("name",       "Name"),
        ("email",      "Email"),
        ("phone",      "Phone"),
        ("experience", "Experience"),
        ("position",   "Position"),
        ("location",   "Location"),
        ("tech_stack", "Tech Stack"),
    ]
    for key, label in field_map:
        val = info.get(key)
        if val:
            if isinstance(val, list):
                val = ", ".join(val)
            lines.append(f"{label}: {val}")
    return "\n".join(lines) if lines else "No information collected yet."
