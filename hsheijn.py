import streamlit as st
import sqlite3
import json
import random
import hashlib
import calendar
from datetime import date
import os

# ======================================================
# CONFIG  — all DB/table names consistent with generators
# ======================================================
DAILY_DB       = "daily_horoscope_prediction.db"   # daily_horoscope_generator.py
MONTHLY_DB     = "monthly_horoscope.db"            # monthly_predictions_generator.py
DAILY_FAQ_DB   = "horoscope_faq.db"
MONTHLY_FAQ_DB = "monthly_faq.db"
POOJA_FILE     = "temple_links.json"

DAILY_TABLE    = "daily_horoscope"    # table inside daily_horoscope_prediction.db
MONTHLY_TABLE  = "monthly_horoscope"  # table inside monthly_horoscope.db

ZODIACS = [
    "Aries","Taurus","Gemini","Cancer","Leo","Virgo",
    "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"
]

COLORS = [
    "Red","Blue","Green","Yellow","White",
    "Pink","Orange","Purple","Brown","Grey","Gold","Silver"
]

today         = date.today()
today_str     = str(today)
year          = today.year
month         = today.month
month_str     = today.strftime("%Y-%m")
month_name    = today.strftime("%B")
days_in_month = calendar.monthrange(year, month)[1]

# ======================================================
# HELPERS
# ======================================================
def get_daily_lucky(sign, date_str):
    h            = hashlib.md5((sign + date_str).encode()).hexdigest()
    color_index  = int(h[:2], 16) % len(COLORS)
    lucky_number = (int(h[2:6], 16) % 9) + 1
    return COLORS[color_index], lucky_number


def format_dates(day_numbers):
    result = []
    for d in day_numbers:
        try:
            full_date = date(year, month, int(d))
            result.append(full_date.strftime("%d %b %Y").lstrip("0") or "0")
        except Exception:
            result.append(str(d))
    return result


# ======================================================
# PAGE CONFIG
# ======================================================
st.set_page_config(page_title="Horoscope Portal", layout="wide")
st.title("🔮 Astrology Portal")

# ======================================================
# SESSION STATES
# ======================================================
if "phase1_sign" not in st.session_state:
    st.session_state.phase1_sign = "Aries"
if "phase1_mode" not in st.session_state:
    st.session_state.phase1_mode = "Daily"
if "phase2_sign" not in st.session_state:
    st.session_state.phase2_sign = "Aries"

# ======================================================
# LOAD POOJA LINKS
# ======================================================
@st.cache_data
def load_poojas():
    if os.path.exists(POOJA_FILE):
        with open(POOJA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

POOJAS = load_poojas()

def get_random_pooja():
    if POOJAS:
        pooja = random.choice(POOJAS)
        return pooja["name"], pooja["link"]
    return "Special Pooja", "https://www.astroved.com/poojas"

# ======================================================
# DATABASE — DAILY PREDICTIONS (Phase 1)
# ======================================================
def get_daily(sign):
    try:
        conn   = sqlite3.connect(DAILY_DB)
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT general, career, love, finance, health,
                   lucky_color, lucky_number,
                   pooja_1_name, pooja_1_link, pooja_1_reason,
                   pooja_2_name, pooja_2_link, pooja_2_reason
            FROM {DAILY_TABLE}
            WHERE date=? AND zodiac_sign=?
        """, (today_str, sign))
        data = cursor.fetchone()
        conn.close()
        return data
    except Exception as e:
        st.error(f"Daily DB error: {e}")
        return None


# ======================================================
# DATABASE — SHORT PREDICTIONS (Phase 1 Monthly)
# ======================================================
def get_monthly(sign):
    try:
        conn   = sqlite3.connect(MONTHLY_DB)
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT general, love, finance, career, business, health, student,
                   auspicious_dates, inauspicious_dates
            FROM {MONTHLY_TABLE}
            WHERE year=? AND month=? AND zodiac_sign=?
        """, (year, month, sign))
        data = cursor.fetchone()
        conn.close()

        if not data:
            return None

        return {
            "general"     : data[0],
            "love"        : data[1],
            "finance"     : data[2],
            "career"      : data[3],
            "business"    : data[4],
            "health"      : data[5],
            "student"     : data[6],
            "auspicious"  : json.loads(data[7]),
            "inauspicious": json.loads(data[8]),
        }
    except Exception as e:
        st.error(f"Monthly DB error: {e}")
        return None


# ======================================================
# DATABASE — ARTICLE CONTENT (Phase 2)
# Uses article_text column with Heading 1/2/3 markers
# ======================================================
def get_monthly_article(sign):
    try:
        conn   = sqlite3.connect(MONTHLY_DB)
        cursor = conn.cursor()

        # Check if article_text column exists
        cursor.execute(f"PRAGMA table_info({MONTHLY_TABLE})")
        cols        = [row[1] for row in cursor.fetchall()]
        has_article = "article_text" in cols

        if has_article:
            cursor.execute(f"""
                SELECT article_text, auspicious_dates, inauspicious_dates
                FROM {MONTHLY_TABLE}
                WHERE year=? AND month=? AND zodiac_sign=?
            """, (year, month, sign))
            data = cursor.fetchone()
            conn.close()

            if data and data[0]:
                return {
                    "article_text": data[0],
                    "auspicious"  : json.loads(data[1]) if data[1] else [],
                    "inauspicious": json.loads(data[2]) if data[2] else [],
                }
        
        conn.close()
        return None
        
    except Exception as e:
        st.error(f"Article DB error: {e}")
        return None


def parse_article_text(article_text):
    """
    Parse article text with Heading 1/2/3 markers into structured sections
    Returns: dict with sections
    """
    sections = {}
    current_h2 = None
    current_h3 = None
    current_content = []
    
    lines = article_text.split('\n')
    
    for line in lines:
        line = line.strip()
        
        if not line:
            continue
            
        if line.startswith("Heading 1:"):
            # Skip title, we'll display it separately
            continue
            
        elif line.startswith("Heading 2:"):
            # Save previous section
            if current_h2:
                key = current_h2.lower().replace(' ', '_').replace('&', 'and')
                sections[key] = '\n\n'.join(current_content)
                current_content = []
            
            current_h2 = line.replace("Heading 2:", "").strip()
            current_h3 = None
            
        elif line.startswith("Heading 3:"):
            # Save previous subsection content if exists
            if current_content and current_h2:
                key = current_h2.lower().replace(' ', '_').replace('&', 'and')
                if key not in sections:
                    sections[key] = '\n\n'.join(current_content)
                else:
                    sections[key] += '\n\n' + '\n\n'.join(current_content)
                current_content = []
            
            current_h3 = line.replace("Heading 3:", "").strip()
            
        else:
            # Regular content
            current_content.append(line)
    
    # Save last section
    if current_h2 and current_content:
        key = current_h2.lower().replace(' ', '_').replace('&', 'and')
        if key not in sections:
            sections[key] = '\n\n'.join(current_content)
        else:
            sections[key] += '\n\n' + '\n\n'.join(current_content)
    
    return sections


def display_article_with_headings(article_text):
    """
    Display article text with proper formatting, converting heading markers to markdown
    """
    lines = article_text.split('\n')
    
    for line in lines:
        line = line.strip()
        
        if not line:
            continue
            
        if line.startswith("Heading 1:"):
            content = line.replace("Heading 1:", "").strip()
            st.markdown(f"# {content}")
            
        elif line.startswith("Heading 2:"):
            content = line.replace("Heading 2:", "").strip()
            st.markdown(f"## {content}")
            
        elif line.startswith("Heading 3:"):
            content = line.replace("Heading 3:", "").strip()
            st.markdown(f"### {content}")
            
        else:
            # Regular paragraph
            st.write(line)


# ======================================================
# DATABASE — FAQs
# ======================================================
def get_daily_faqs(sign):
    if not os.path.exists(DAILY_FAQ_DB):
        return []
    try:
        conn   = sqlite3.connect(DAILY_FAQ_DB)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT question, answer FROM daily_faq
            WHERE date=? AND moon_sign=?
            ORDER BY id ASC
        """, (today_str, sign))
        rows = cursor.fetchall()
        conn.close()
        return [{"question": r[0], "answer": r[1]} for r in rows]
    except Exception:
        return []


def get_monthly_faqs(sign):
    if not os.path.exists(MONTHLY_FAQ_DB):
        return []
    try:
        conn   = sqlite3.connect(MONTHLY_FAQ_DB)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT question, answer FROM monthly_faq
            WHERE month=? AND moon_sign=?
            ORDER BY id ASC
        """, (month_str, sign))
        rows = cursor.fetchall()
        conn.close()
        return [{"question": r[0], "answer": r[1]} for r in rows]
    except Exception:
        return []


def render_faqs(faqs, label="FAQs"):
    if not faqs:
        st.info(f"No {label} available yet. Run the FAQ generator script first.")
        return
    st.markdown(f"### 🙋 {label}")
    for faq in faqs:
        with st.expander(f"❓ {faq['question']}"):
            st.write(faq["answer"])


# ======================================================
# TABS
# ======================================================
tab1, tab2 = st.tabs(["Phase 1 : Predictions", "Phase 2 : Articles"])

# ======================================================
# TAB 1 — PHASE 1
# ======================================================
with tab1:

    st.header("Horoscope Predictions")

    st.session_state.phase1_sign = st.selectbox(
        "Select Zodiac Sign",
        ZODIACS,
        index=ZODIACS.index(st.session_state.phase1_sign),
        key="p1_zodiac"
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Daily Horoscope", key="p1_daily"):
            st.session_state.phase1_mode = "Daily"
    with col2:
        if st.button("Monthly Horoscope", key="p1_monthly"):
            st.session_state.phase1_mode = "Monthly"

    sign = st.session_state.phase1_sign
    mode = st.session_state.phase1_mode

    st.markdown("---")

    # ── DAILY ──────────────────────────────────────────────────
    if mode == "Daily":
        st.subheader(f"{sign} Daily Horoscope — {today_str}")

        data          = get_daily(sign)
        color, number = get_daily_lucky(sign, today_str)

        if data:
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("### General")
                st.write(data[0])
                st.markdown("### Career")
                st.write(data[1])
                st.markdown("### Relationships")
                st.write(data[2])
            with col2:
                st.markdown("### Finance")
                st.write(data[3])
                st.markdown("### Health")
                st.write(data[4])
                st.success(f"Lucky Color: {color}")
                st.success(f"Lucky Number: {number}")
                st.markdown("### 🪔 Today's Recommended Poojas")
                p1_name, p1_link, p1_reason = data[7], data[8], data[9]
                p2_name, p2_link, p2_reason = data[10], data[11], data[12]
                if p1_name and p1_link:
                    st.markdown(f"**1. [{p1_name}]({p1_link})**")
                    if p1_reason:
                        st.caption(p1_reason)
                if p2_name and p2_link:
                    st.markdown(f"**2. [{p2_name}]({p2_link})**")
                    if p2_reason:
                        st.caption(p2_reason)
                if not p1_name and not p2_name:
                    st.info("Pooja recommendation not available.")
        else:
            st.warning("Daily horoscope not generated yet.")

        st.markdown("---")
        render_faqs(get_daily_faqs(sign), label="Daily FAQs")

    # ── MONTHLY ────────────────────────────────────────────────
    else:
        st.subheader(f"{sign} Monthly Horoscope — {month_name} {year}")

        data = get_monthly(sign)

        if data:
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("### General")
                st.write(data["general"])
                st.markdown("### Love")
                st.write(data["love"])
                st.markdown("### Finance")
                st.write(data["finance"])
                st.markdown("### Career")
                st.write(data["career"])
            with col2:
                st.markdown("### Business")
                st.write(data["business"])
                st.markdown("### Health")
                st.write(data["health"])
                st.markdown("### Student")
                st.write(data["student"])
                st.markdown("### 🌟 Auspicious Dates")
                st.write(", ".join(format_dates(data["auspicious"])))
                st.markdown("### ⚠️ Inauspicious Dates")
                st.write(", ".join(format_dates(data["inauspicious"])))
        else:
            st.warning("Monthly horoscope not generated yet.")

        st.markdown("---")
        render_faqs(get_monthly_faqs(sign), label="Monthly FAQs")


# ======================================================
# TAB 2 — PHASE 2 (Updated for article_text format)
# ======================================================
with tab2:

    st.header("Monthly Horoscope Article")

    st.session_state.phase2_sign = st.selectbox(
        "Select Zodiac Sign for Article",
        ZODIACS,
        index=ZODIACS.index(st.session_state.phase2_sign),
        key="p2_zodiac"
    )

    sign = st.session_state.phase2_sign

    st.markdown("---")

    data = get_monthly_article(sign)

    if data and data.get("article_text"):
        st.subheader(f"{sign} — {month_name} {year} Horoscope Article")
        
        # Display the article with proper heading formatting
        display_article_with_headings(data["article_text"])
        
        st.markdown("---")
        
        # Display dates at the bottom
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### 🌟 Auspicious Dates")
            if data["auspicious"]:
                for d in format_dates(data["auspicious"]):
                    st.markdown(f"- ✅ {d}")
            else:
                st.info("Check back soon for auspicious dates")
        with col2:
            st.markdown("### ⚠️ Inauspicious Dates")
            if data["inauspicious"]:
                for d in format_dates(data["inauspicious"]):
                    st.markdown(f"- 🚫 {d}")
            else:
                st.info("Check back soon for inauspicious dates")
                
        # Add random pooja recommendation at the end
        st.markdown("---")
        pooja_name, pooja_link = get_random_pooja()
        st.markdown(f"### 🪔 Divine Recommendation")
        st.markdown(f"**[{pooja_name}]({pooja_link})**")
        st.caption("Click to book this special pooja for enhanced blessings")
        
    else:
        st.warning("Article content not available. Run monthly_article_generator_fixed.py first.")
        st.info("Steps to generate articles:")
        st.code("""
1. Run: python monthly_article_generator_fixed.py
2. Wait for all 12 zodiac articles to generate
3. Refresh this page
        """) 