import streamlit as st
import sqlite3
import json
import random
import hashlib
from datetime import date

# ======================================================
# CONFIG
# ======================================================
DAILY_DB    = "daily_horoscope.db"
MONTHLY_DB  = "monthly_horoscope.db"
DAILY_FAQ_DB   = "horoscope_faq.db"      # daily FAQ db
MONTHLY_FAQ_DB = "monthly_faq.db"        # monthly FAQ db
POOJA_FILE  = "temple_links.json"

ZODIACS = [
    "Aries","Taurus","Gemini","Cancer","Leo","Virgo",
    "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"
]

COLORS = [
    "Red","Blue","Green","Yellow","White",
    "Pink","Orange","Purple","Brown","Grey","Gold","Silver"
]

today     = date.today()
today_str = str(today)
year      = today.year
month     = today.month
month_str = today.strftime("%Y-%m")   # for monthly FAQ DB lookup

# ======================================================
# LUCKY COLOR / NUMBER
# ======================================================
def get_daily_lucky(sign, date_str):
    h            = hashlib.md5((sign + date_str).encode()).hexdigest()
    color_index  = int(h[:2], 16) % len(COLORS)
    lucky_number = (int(h[2:6], 16) % 9) + 1
    return COLORS[color_index], lucky_number

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
    with open(POOJA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

POOJAS = load_poojas()

def get_random_pooja():
    pooja = random.choice(POOJAS)
    return pooja["name"], pooja["link"]

# ======================================================
# DATABASE FUNCTIONS — HOROSCOPE
# ======================================================
def get_daily(sign):
    conn   = sqlite3.connect(DAILY_DB)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT general, career, love, finance, health,
               lucky_color, lucky_number
        FROM daily_horoscope
        WHERE date=? AND zodiac_sign=?
    """, (today_str, sign))
    data = cursor.fetchone()
    conn.close()
    return data


def get_monthly(sign):
    conn   = sqlite3.connect(MONTHLY_DB)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT general, love, finance, career, business, health, student,
               auspicious_dates, inauspicious_dates
        FROM monthly_horoscope
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
        "inauspicious": json.loads(data[8])
    }

# ======================================================
# DATABASE FUNCTIONS — FAQs
# ======================================================
def get_daily_faqs(sign):
    """Fetch today's FAQs for a sign from daily FAQ DB."""
    if not __import__("os").path.exists(DAILY_FAQ_DB):
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
    """Fetch this month's FAQs for a sign from monthly FAQ DB."""
    if not __import__("os").path.exists(MONTHLY_FAQ_DB):
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
    """Render FAQ list as expanders."""
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
# TAB 1 — PHASE 1  (Predictions + FAQs)
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

    # ── DAILY ──────────────────────────────────────────
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
        else:
            st.warning("Daily horoscope not generated yet.")

        st.markdown("---")

        # Daily FAQs
        daily_faqs = get_daily_faqs(sign)
        render_faqs(daily_faqs, label="Daily FAQs")

    # ── MONTHLY ────────────────────────────────────────
    else:
        st.subheader(f"{sign} Monthly Horoscope — {month}/{year}")

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
                st.write(", ".join(map(str, data["auspicious"])))

                st.markdown("### ⚠️ Inauspicious Dates")
                st.write(", ".join(map(str, data["inauspicious"])))
        else:
            st.warning("Monthly horoscope not generated yet.")

        st.markdown("---")

        # Monthly FAQs
        monthly_faqs = get_monthly_faqs(sign)
        render_faqs(monthly_faqs, label="Monthly FAQs")

# ======================================================
# TAB 2 — PHASE 2  (Articles — unchanged)
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

    data = get_monthly(sign)

    if data:
        st.subheader(f"{sign} Article — {month}/{year}")

        sections = [
            ("General",       data["general"]),
            ("Relationships", data["love"]),
            ("Finances",      data["finance"]),
            ("Career",        data["career"]),
            ("Business",      data["business"]),
            ("Health",        data["health"]),
            ("Education",     data["student"])
        ]

        for title, content in sections:
            pooja_name, pooja_link = get_random_pooja()

            st.markdown(f"### {title}")
            st.write(content)

            st.markdown(
                f"**Divine technique to improve your {title}: "
                f"[{pooja_name}]({pooja_link})**"
            )

        st.markdown("### 🌟 Auspicious Dates")
        st.write(", ".join(map(str, data["auspicious"])))

        st.markdown("### ⚠️ Inauspicious Dates")
        st.write(", ".join(map(str, data["inauspicious"])))

    else:
        st.warning("Monthly data not available.")