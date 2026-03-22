"""
app.py
══════
TalentScout AI — Two-page Streamlit application.

Page 1  ──  Candidate Profile Form
            All personal & professional details collected here
            before the interview begins.

Page 2  ──  AI Technical Interview Chat
            Groq-powered chat that immediately asks technical
            questions based on the submitted tech stack.
"""

import html as html_lib
import time
from pathlib import Path

import streamlit as st

from chatbot      import TalentScoutBot
from data_handler import DataHandler
from llm_handler  import get_model_info
from utils        import (
    format_tech_tags,
    format_message_html,
    validate_email,
    validate_phone,
    parse_tech_stack,
)

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE CONFIG  (must be first Streamlit call)
# ═══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title = "TalentScout AI",
    page_icon  = "🎯",
    layout     = "wide",
    initial_sidebar_state = "expanded",
)


# ═══════════════════════════════════════════════════════════════════════════════
# CSS INJECTION
# ═══════════════════════════════════════════════════════════════════════════════
def _inject_css() -> None:
    css_path = Path("assets/styles.css")
    if css_path.exists():
        st.markdown(
            f"<style>{css_path.read_text(encoding='utf-8')}</style>",
            unsafe_allow_html=True,
        )

_inject_css()


# ═══════════════════════════════════════════════════════════════════════════════
# SESSION STATE DEFAULTS
# ═══════════════════════════════════════════════════════════════════════════════
if "page"              not in st.session_state: st.session_state.page              = "form"
if "input_key"         not in st.session_state: st.session_state.input_key         = 0
if "messages"          not in st.session_state: st.session_state.messages          = []
if "bot"               not in st.session_state: st.session_state.bot               = None
if "show_closing_popup" not in st.session_state: st.session_state.show_closing_popup = False
if "closing_message"   not in st.session_state: st.session_state.closing_message   = ""


# ═══════════════════════════════════════════════════════════════════════════════
# SHARED RENDER HELPERS  (used by both pages)
# ═══════════════════════════════════════════════════════════════════════════════

def _render_bot_bubble(content: str) -> None:
    safe = format_message_html(content, is_bot=True)
    st.markdown(
        f"""
        <div class="bot-bubble">
            <div class="bot-avatar">🤖</div>
            <div class="bot-content">
                <div class="bot-name">TalentScout AI</div>
                <div class="bot-message">{safe}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_user_bubble(content: str) -> None:
    safe = format_message_html(content, is_bot=False)
    st.markdown(
        f"""
        <div class="user-bubble">
            <div class="user-content">
                <div class="user-name">You</div>
                <div class="user-message">{safe}</div>
            </div>
            <div class="user-avatar">👤</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _show_closing_page() -> None:
    """
    Dedicated full-page closing view shown after all technical questions are answered.
    Uses Streamlit-native layout (columns + st.button) — no CSS position:fixed needed.
    """
    bot     = st.session_state.bot
    info    = bot.candidate_info
    name    = info.get("name", "Candidate")
    message = st.session_state.closing_message

    # ── Sidebar ───────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown(
            """
            <div class="sidebar-logo">
                <div class="sidebar-logo-icon">🎯</div>
                <div class="sidebar-title">TalentScout AI</div>
                <div class="sidebar-sub">Intelligent Hiring Assistant</div>
            </div>
            <div class="sidebar-hr"></div>
            <div class="how-it-works">
                <div class="hiw-step">
                    <div class="hiw-num hiw-done">✓</div>
                    <div class="hiw-text hiw-text-dim">
                        <div class="hiw-title">Profile</div>
                        <div class="hiw-desc">Completed</div>
                    </div>
                </div>
                <div class="hiw-connector"></div>
                <div class="hiw-step">
                    <div class="hiw-num hiw-done">✓</div>
                    <div class="hiw-text hiw-text-dim">
                        <div class="hiw-title">Technical Interview</div>
                        <div class="hiw-desc">Completed</div>
                    </div>
                </div>
            </div>
            <div class="sidebar-hr"></div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄  Start New Interview", use_container_width=True, key="closing_sidebar_btn"):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()

    # ── Page header ───────────────────────────────────────────────────────────
    st.markdown(
        """
        <div style="text-align:center; padding: 2.5rem 0 1.5rem;">
            <div style="font-size:50px; margin-bottom:10px;">🎯</div>
            <div class="app-title">TalentScout AI</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Centered closing card ─────────────────────────────────────────────────
    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        safe_name = html_lib.escape(name)
        safe_msg  = format_message_html(message, is_bot=True)

        st.markdown(
            f"""
            <div class="closing-card">
                <div class="closing-icon">🎉</div>
                <div class="closing-title">Interview Complete!</div>
                <div class="closing-subtitle">
                    Great work, <strong style="color:#a78bfa;">{safe_name}</strong>!
                </div>
                <div class="closing-message">{safe_msg}</div>
                <div class="closing-meta">
                    <span>📅</span>
                    Expected response within
                    <span class="closing-meta-pill">3 – 5 business days</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)
        if st.button("🔄  Start New Interview", use_container_width=True, key="closing_main_btn"):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()


def _render_typing() -> st.delta_generator.DeltaGenerator:
    ph = st.empty()
    ph.markdown(
        """
        <div class="typing-wrapper">
            <div class="bot-avatar">🤖</div>
            <div class="typing-bubble">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    return ph


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 1 — CANDIDATE PROFILE FORM
# ═══════════════════════════════════════════════════════════════════════════════

def _show_form() -> None:

    # ── Sidebar ───────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown(
            """
            <div class="sidebar-logo">
                <div class="sidebar-logo-icon">🎯</div>
                <div class="sidebar-title">TalentScout AI</div>
                <div class="sidebar-sub">Intelligent Hiring Assistant</div>
            </div>
            <div class="sidebar-hr"></div>
            <div class="section-label">How it works</div>
            <div class="how-it-works">
                <div class="hiw-step">
                    <div class="hiw-num hiw-active">1</div>
                    <div class="hiw-text">
                        <div class="hiw-title">Your Profile</div>
                        <div class="hiw-desc">Fill in your details & tech stack</div>
                    </div>
                </div>
                <div class="hiw-connector"></div>
                <div class="hiw-step">
                    <div class="hiw-num hiw-inactive">2</div>
                    <div class="hiw-text hiw-text-dim">
                        <div class="hiw-title">Technical Interview</div>
                        <div class="hiw-desc">AI asks questions from your stack</div>
                    </div>
                </div>
            </div>
            <div class="sidebar-hr"></div>
            <div class="info-card" style="text-align:center; color:rgba(167,139,250,0.5); font-size:12px; line-height:1.7;">
                ⏱️ Takes about <strong style="color:#a78bfa;">10–15 minutes</strong><br>
                All answers are reviewed by our hiring team.
            </div>
            """,
            unsafe_allow_html=True,
        )
    # ── Page header ───────────────────────────────────────────────────────────
    st.markdown(
        """
        <div class="form-page-header">
            <div style="font-size:50px; margin-bottom:10px;">🎯</div>
            <div class="app-title">TalentScout AI</div>
            <div class="app-subtitle">Intelligent Hiring Assistant — Powered by Groq & Llama 3</div>
            <div class="steps-bar">
                <div class="step-item">
                    <div class="step-circle step-circle-active">1</div>
                    <span class="step-lbl step-lbl-active">Your Profile</span>
                </div>
                <div class="step-line"></div>
                <div class="step-item">
                    <div class="step-circle step-circle-inactive">2</div>
                    <span class="step-lbl step-lbl-inactive">Technical Interview</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Centered form card ────────────────────────────────────────────────────
    _, mid, _ = st.columns([0.5, 3, 0.5])

    with mid:
        st.markdown('<div class="form-card">', unsafe_allow_html=True)

        st.markdown(
            """
            <div class="form-card-head">
                <div class="form-card-title">Tell us about yourself</div>
                <div class="form-card-sub">
                    Complete your profile to start the AI-powered screening interview
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # ── Section: Personal Information ─────────────────────────────────────
        st.markdown('<div class="form-section">👤 &nbsp;Personal Information</div>', unsafe_allow_html=True)

        with st.form("candidate_form", clear_on_submit=False):

            name = st.text_input(
                "Full Name *",
                placeholder="e.g. Jane Doe",
                key="fi_name",
            )

            col_email, col_phone = st.columns(2)
            with col_email:
                email = st.text_input(
                    "Email Address *",
                    placeholder="jane@company.com",
                    key="fi_email",
                )
            with col_phone:
                phone = st.text_input(
                    "Phone Number *",
                    placeholder="+1 555 000 1234",
                    key="fi_phone",
                )

            # ── Section: Professional Details ─────────────────────────────────
            st.markdown('<div class="form-section" style="margin-top:1.2rem;">💼 &nbsp;Professional Details</div>', unsafe_allow_html=True)

            col_exp, col_pos = st.columns(2)
            with col_exp:
                experience = st.text_input(
                    "Years of Experience *",
                    placeholder="e.g. 3 years",
                    key="fi_exp",
                )
            with col_pos:
                position = st.text_input(
                    "Desired Position(s) *",
                    placeholder="e.g. Backend Engineer",
                    key="fi_pos",
                )

            location = st.text_input(
                "Current Location *",
                placeholder="e.g. Austin, Texas, USA",
                key="fi_loc",
            )

            # ── Section: Technical Profile ────────────────────────────────────
            st.markdown('<div class="form-section" style="margin-top:1.2rem;">⚡ &nbsp;Technical Profile</div>', unsafe_allow_html=True)

            tech_stack_raw = st.text_area(
                "Tech Stack *",
                placeholder=(
                    "List all technologies, languages, frameworks & tools you work with.\n"
                    "e.g. Python, Django, PostgreSQL, React, Docker, AWS, Git"
                ),
                height=110,
                key="fi_tech",
                help="Separate technologies with commas. The more detail, the better your questions will be.",
            )

            # ── Submit ────────────────────────────────────────────────────────
            st.markdown("<div style='margin-top: 0.5rem;'></div>", unsafe_allow_html=True)
            submitted = st.form_submit_button(
                "🚀  Start My Interview",
                use_container_width=True,
                type="primary",
            )

        # ── Validation & transition ────────────────────────────────────────────
        if submitted:
            errors = _validate_form(name, email, phone, experience, position, location, tech_stack_raw)

            if errors:
                for msg in errors:
                    st.markdown(
                        f'<div class="form-error">⚠️ &nbsp;{html_lib.escape(msg)}</div>',
                        unsafe_allow_html=True,
                    )
            else:
                techs          = parse_tech_stack(tech_stack_raw)
                candidate_info = {
                    "name":       name.strip(),
                    "email":      email.strip().lower(),
                    "phone":      phone.strip(),
                    "experience": experience.strip(),
                    "position":   position.strip(),
                    "location":   location.strip(),
                    "tech_stack": techs,
                }
                with st.spinner("✨ Generating your personalised technical questions…"):
                    dh        = DataHandler()
                    bot       = TalentScoutBot(data_handler=dh)
                    first_msg = bot.initialize_with_form_data(candidate_info)

                st.session_state.bot          = bot
                st.session_state.data_handler = dh
                st.session_state.messages     = [{"role": "assistant", "content": first_msg}]
                st.session_state.page         = "chat"
                st.session_state.input_key    = 0
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)   # close .form-card


def _validate_form(name, email, phone, experience, position, location, tech_raw) -> list[str]:
    errors = []
    if not name.strip() or len(name.strip()) < 2:
        errors.append("Please enter your full name (at least 2 characters).")
    if not validate_email(email.strip()):
        errors.append("Please enter a valid email address (e.g. jane@company.com).")
    if not validate_phone(phone.strip()):
        errors.append("Please enter a valid phone number (7–15 digits, country code optional).")
    if not experience.strip():
        errors.append("Please specify your years of experience.")
    if not position.strip():
        errors.append("Please specify the desired position.")
    if not location.strip():
        errors.append("Please enter your current location.")
    if not tech_raw.strip():
        errors.append("Please list at least one technology in your tech stack.")
    return errors


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 2 — AI TECHNICAL INTERVIEW CHAT
# ═══════════════════════════════════════════════════════════════════════════════

def _show_chat() -> None:
    bot  = st.session_state.bot
    info = bot.candidate_info

    # ── Sidebar ───────────────────────────────────────────────────────────────
    with st.sidebar:
        # Logo
        st.markdown(
            """
            <div class="sidebar-logo">
                <div class="sidebar-logo-icon">🎯</div>
                <div class="sidebar-title">TalentScout AI</div>
                <div class="sidebar-sub">Intelligent Hiring Assistant</div>
            </div>
            <div class="sidebar-hr"></div>
            """,
            unsafe_allow_html=True,
        )

        # Step indicator — show "Done" on both steps when interview is complete
        interview_done = st.session_state.show_closing_popup
        step2_num   = "✓" if interview_done else "2"
        step2_cls   = "hiw-done" if interview_done else "hiw-active"
        step2_text  = "hiw-text-dim" if interview_done else "hiw-text"
        step2_desc  = "Completed" if interview_done else "In progress"

        st.markdown(
            f"""
            <div class="how-it-works">
                <div class="hiw-step">
                    <div class="hiw-num hiw-done">✓</div>
                    <div class="hiw-text hiw-text-dim">
                        <div class="hiw-title">Profile</div>
                        <div class="hiw-desc">Completed</div>
                    </div>
                </div>
                <div class="hiw-connector"></div>
                <div class="hiw-step">
                    <div class="hiw-num {step2_cls}">{step2_num}</div>
                    <div class="{step2_text}">
                        <div class="hiw-title">Technical Interview</div>
                        <div class="hiw-desc">{step2_desc}</div>
                    </div>
                </div>
            </div>
            <div class="sidebar-hr"></div>
            """,
            unsafe_allow_html=True,
        )

        # Q&A progress
        total_q = len(bot.tech_questions)
        done_q  = bot.current_question_index
        q_pct   = int(done_q / total_q * 100) if total_q else 0

        st.markdown(
            f"""
            <div class="progress-wrapper">
                <div class="progress-header">
                    <span class="progress-title">Interview Progress</span>
                    <span class="progress-pct">{q_pct}%</span>
                </div>
                <div class="progress-track">
                    <div class="progress-fill" style="width:{q_pct}%;"></div>
                </div>
                <div style="margin-top:6px; text-align:center;">
                    <span class="stage-pill">❓ {done_q} of {total_q} questions answered</span>
                </div>
            </div>
            <div class="sidebar-hr"></div>
            """,
            unsafe_allow_html=True,
        )

        # Candidate profile (fully populated from the form)
        st.markdown('<div class="section-label">Candidate Profile</div>', unsafe_allow_html=True)

        fields = [
            ("👤", "Name",       info.get("name")),
            ("📧", "Email",      info.get("email")),
            ("📱", "Phone",      info.get("phone")),
            ("💼", "Experience", info.get("experience")),
            ("🎯", "Position",   info.get("position")),
            ("📍", "Location",   info.get("location")),
        ]
        for icon, lbl, val in fields:
            if val:
                st.markdown(
                    f"""
                    <div class="info-card">
                        <div class="info-field-label">{icon} {lbl}</div>
                        <div class="info-field-value">{html_lib.escape(str(val))}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        tech = info.get("tech_stack")
        if tech:
            tags = format_tech_tags(tech if isinstance(tech, list) else [tech])
            st.markdown(
                f"""
                <div class="info-card">
                    <div class="info-field-label">⚡ Tech Stack</div>
                    <div style="margin-top:6px;">{tags}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Restart button
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄  Start Over", use_container_width=True):
            for k in ["bot", "messages", "data_handler", "input_key", "page"]:
                st.session_state.pop(k, None)
            st.rerun()

    # ── Main chat area ────────────────────────────────────────────────────────
    st.markdown(
        """
        <div style="text-align:center; padding: 1.2rem 0 0.5rem;">
            <div class="app-title">Technical Interview</div>
            <div class="app-subtitle">
                Answer each question as clearly as you can — there's no rush 🧠
            </div>
        </div>
        <hr class="header-divider">
        """,
        unsafe_allow_html=True,
    )

    # Render chat history
    chat_area = st.container()
    with chat_area:
        for msg in st.session_state.messages:
            if msg["role"] == "assistant":
                _render_bot_bubble(msg["content"])
            else:
                _render_user_bubble(msg["content"])

    # Chat input
    prompt = st.chat_input(
        placeholder="Type your answer here…",
        key=f"chat_{st.session_state.input_key}",
    )

    if prompt and prompt.strip():
        st.session_state.messages.append({"role": "user", "content": prompt.strip()})

        with chat_area:
            _render_user_bubble(prompt.strip())
            typing_ph = _render_typing()
            time.sleep(0.5)
            response  = bot.process(prompt.strip())
            typing_ph.empty()

        if bot.stage == "closing":
            # ── Interview is done: show popup, NOT a chat bubble ──────────────
            st.session_state.show_closing_popup = True
            st.session_state.closing_message    = response
        else:
            # ── Normal turn: add to chat as usual ─────────────────────────────
            st.session_state.messages.append({"role": "assistant", "content": response})
            with chat_area:
                _render_bot_bubble(response)

        st.session_state.input_key += 1
        st.rerun()



# ═══════════════════════════════════════════════════════════════════════════════
# ROUTER
# ═══════════════════════════════════════════════════════════════════════════════
if st.session_state.page == "form":
    _show_form()
elif st.session_state.show_closing_popup:
    _show_closing_page()
else:
    _show_chat()
