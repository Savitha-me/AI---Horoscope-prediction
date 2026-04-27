import streamlit as st
import sqlite3
import json
import hashlib
from datetime import date
import os

# ======================================================
# CONFIG
# ======================================================
DAILY_DB       = "daily_horoscope_prediction.db"
MONTHLY_DB     = "monthly_horoscope.db"
DAILY_FAQ_DB   = "horoscope_faq.db"
MONTHLY_FAQ_DB = "monthly_faq.db"
POOJA_FILE     = "temple_links.json"

ZODIACS = [
    "Aries","Taurus","Gemini","Cancer","Leo","Virgo",
    "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"
]

today      = date.today()
today_str  = str(today)
year       = today.year
month      = today.month
month_str  = today.strftime("%Y-%m")
month_name = today.strftime("%B")

# ======================================================
# LOAD POOJAS
# ======================================================
@st.cache_data
def load_poojas():
    if os.path.exists(POOJA_FILE):
        with open(POOJA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

POOJAS      = load_poojas()
POOJA_MAP   = {p["name"]: p["link"] for p in POOJAS}
POOJA_NAMES = list(POOJA_MAP.keys())

# ======================================================
# POOJA RECOMMENDATION LOGIC
# Deterministic hash-based — no randomness
#   Daily   → seed = sign + date      → changes every day
#   Monthly → seed = sign + year+month → changes every month
#   Article → seed = sign + heading + year+month → unique per section
# ======================================================
def _pick_pooja(seed: str, offset: int = 0) -> tuple:
    h     = hashlib.md5(f"{seed}_{offset}".encode()).hexdigest()
    index = int(h[:8], 16) % len(POOJA_NAMES)
    name  = POOJA_NAMES[index]
    return name, POOJA_MAP[name]

def get_daily_poojas(sign: str) -> list:
    seed         = f"{sign}_{today_str}"
    name1, link1 = _pick_pooja(seed, 0)
    name2, link2 = _pick_pooja(seed, 1)
    attempts     = 2
    while name2 == name1 and attempts < 20:
        name2, link2 = _pick_pooja(seed, attempts)
        attempts += 1
    return [
        {"name": name1, "link": link1,
         "reason": f"Performing {name1} today will help {sign} natives overcome daily challenges and attract positive energy."},
        {"name": name2, "link": link2,
         "reason": f"{name2} is especially beneficial for {sign} today to strengthen your planetary influences."},
    ]

def get_monthly_poojas(sign: str) -> list:
    seed         = f"{sign}_{year}_{month}"
    name1, link1 = _pick_pooja(seed, 0)
    name2, link2 = _pick_pooja(seed, 1)
    attempts     = 2
    while name2 == name1 and attempts < 20:
        name2, link2 = _pick_pooja(seed, attempts)
        attempts += 1
    return [
        {"name": name1, "link": link1,
         "reason": f"Performing {name1} this month will support {sign} natives in achieving their monthly goals and maintaining harmony."},
        {"name": name2, "link": link2,
         "reason": f"{name2} is highly recommended for {sign} in {month_name} to enhance prosperity and well-being."},
    ]

def get_section_pooja(sign: str, heading: str) -> tuple:
    seed = f"{sign}_{heading.lower().strip()}_{year}_{month}"
    return _pick_pooja(seed, 0)

# ======================================================
# HELPERS
# ======================================================
COLORS = [
    "Red","Blue","Green","Yellow","White",
    "Pink","Orange","Purple","Brown","Grey","Gold","Silver"
]

def get_daily_lucky(sign):
    h            = hashlib.md5((sign + today_str).encode()).hexdigest()
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
# DATABASE — DAILY
# ======================================================
def fetch_daily(sign):
    try:
        conn = sqlite3.connect(DAILY_DB)
        cur  = conn.cursor()
        cur.execute("""
            SELECT general, career, love, finance, health,
                   lucky_color, lucky_number,
                   pooja_1_name, pooja_1_link, pooja_1_reason,
                   pooja_2_name, pooja_2_link, pooja_2_reason
            FROM daily_horoscope
            WHERE zodiac_sign=? AND date=?
        """, (sign, today_str))
        row = cur.fetchone()
        conn.close()
        return row
    except Exception as e:
        st.error(f"Daily DB error: {e}")
        return None

# ======================================================
# DATABASE — MONTHLY SHORT PREDICTIONS
# ======================================================
def fetch_monthly(sign):
    try:
        conn = sqlite3.connect(MONTHLY_DB)
        cur  = conn.cursor()
        cur.execute("""
            SELECT general, love, finance, career, business, health, student,
                   auspicious_dates, inauspicious_dates
            FROM monthly_horoscope
            WHERE zodiac_sign=? AND year=? AND month=?
        """, (sign, year, month))
        row = cur.fetchone()
        conn.close()
        if not row:
            return None
        return {
            "general"     : row[0],
            "love"        : row[1],
            "finance"     : row[2],
            "career"      : row[3],
            "business"    : row[4],
            "health"      : row[5],
            "student"     : row[6],
            "auspicious"  : json.loads(row[7]),
            "inauspicious": json.loads(row[8]),
        }
    except Exception as e:
        st.error(f"Monthly DB error: {e}")
        return None

# ======================================================
# DATABASE — ARTICLE
# Tries article_text column in monthly_horoscope.db first.
# Falls back to reading the 7 section columns and building
# a simple article structure so Phase 2 is never blank.
# ======================================================
def fetch_article(sign):
    # Guard: if DB file missing, return None (do not create empty DB)
    if not os.path.exists(MONTHLY_DB):
        return None

    conn         = None
    article_text = None

    try:
        conn = sqlite3.connect(MONTHLY_DB)
        cur  = conn.cursor()

        # Check what columns exist
        cur.execute("PRAGMA table_info(monthly_horoscope)")
        cols = [c[1] for c in cur.fetchall()]

        # Table does not exist yet
        if not cols:
            return None

        # Try article_text column first
        if "article_text" in cols:
            cur.execute("""
                SELECT article_text FROM monthly_horoscope
                WHERE zodiac_sign=? AND year=? AND month=?
            """, (sign, year, month))
            row = cur.fetchone()
            if row and row[0] and row[0].strip():
                article_text = row[0]

        # Fallback: build article from 7 section columns
        if not article_text:
            cur.execute("""
                SELECT general, love, finance, career, business, health, student
                FROM monthly_horoscope
                WHERE zodiac_sign=? AND year=? AND month=?
            """, (sign, year, month))
            row = cur.fetchone()

            if row:
                def clean(text):
                    if not text:
                        return ""
                    lines = [l for l in text.split("\n")
                             if not l.strip().lower().startswith("divine technique")
                             and not l.strip().lower().startswith("remedy:")]
                    return "\n".join(lines).strip()

                sections = [
                    ("Overview",                    clean(row[0])),
                    ("Love & Relationships",         clean(row[1])),
                    ("Finance & Wealth",             clean(row[2])),
                    ("Career & Professional Growth", clean(row[3])),
                    ("Business",                     clean(row[4])),
                    ("Health & Wellness",            clean(row[5])),
                    ("Education & Learning",         clean(row[6])),
                ]

                built = [f"Heading 1: {sign} Monthly Horoscope - {month_name} {year}", ""]
                for heading, content in sections:
                    built.append(f"Heading 2: {heading}")
                    built.append("")
                    if content:
                        built.append(content)
                    built.append("")

                article_text = "\n".join(built)

    except Exception as e:
        st.error(f"Article fetch error: {e}")
    finally:
        if conn:
            conn.close()

    return article_text

# ======================================================
# FAQs
# ======================================================
def fetch_daily_faq(sign):
    if not os.path.exists(DAILY_FAQ_DB):
        return []
    try:
        conn = sqlite3.connect(DAILY_FAQ_DB)
        cur  = conn.cursor()
        cur.execute("""
            SELECT question, answer FROM daily_faq
            WHERE moon_sign=? AND date=?
        """, (sign, today_str))
        data = cur.fetchall()
        conn.close()
        return data
    except Exception:
        return []

def fetch_monthly_faq(sign):
    if not os.path.exists(MONTHLY_FAQ_DB):
        return []
    try:
        conn = sqlite3.connect(MONTHLY_FAQ_DB)
        cur  = conn.cursor()
        cur.execute("""
            SELECT question, answer FROM monthly_faq
            WHERE moon_sign=? AND month=?
        """, (sign, f"{year}-{month:02d}"))
        data = cur.fetchall()
        conn.close()
        return data
    except Exception:
        return []

# ======================================================
# RENDER POOJA CARD
# ======================================================
def render_pooja_card(index: int, pooja: dict):
    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, #fff8e7, #fdf3d0);
            border-left: 4px solid #d4a017;
            border-radius: 8px;
            padding: 12px 16px;
            margin: 8px 0;
        ">
            <span style="font-size:1.1em;">🪔</span>
            <strong>{index}.&nbsp;<a href="{pooja['link']}" target="_blank"
               style="color:#b5650d; text-decoration:underline;">
               {pooja['name']}</a></strong><br>
            <span style="color:#555; font-size:0.92em;">{pooja['reason']}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ======================================================
# DISPLAY ARTICLE — Heading 1/2/3 with unique pooja per H2
# ======================================================
def display_article(sign, text):
    lines          = text.split("\n")
    current_h2     = None
    section_buffer = []

    def flush_section():
        for ln in section_buffer:
            s = ln.strip()
            if not s:
                continue
            if s.lower().startswith("divine technique") or s.lower().startswith("remedy:"):
                continue
            if s.startswith("Heading 3:"):
                st.markdown(f"### {s.replace('Heading 3:', '').strip()}")
            else:
                st.write(s)

        # Unique pooja for this H2 section
        if current_h2:
            name, link = get_section_pooja(sign, current_h2)
            st.markdown(
                f"*🪔 Divine technique to improve your {current_h2}:* "
                f"**[{name}]({link})**"
            )
        section_buffer.clear()

    for line in lines:
        s = line.strip()
        if not s:
            continue

        if s.startswith("Heading 1:"):
            st.markdown(f"# {s.replace('Heading 1:', '').strip()}")

        elif s.startswith("Heading 2:"):
            if current_h2 is not None:
                flush_section()
            current_h2 = s.replace("Heading 2:", "").strip()
            st.markdown(f"## {current_h2}")

        else:
            section_buffer.append(line)

    if current_h2 is not None:
        flush_section()

# ======================================================
# UI
# ======================================================
st.set_page_config(layout="wide")
st.title("🔮 AI Horoscope Portal")

tab1, tab2 = st.tabs(["Phase 1 : Predictions", "Phase 2 : Articles"])

# ======================================================
# PHASE 1
# ======================================================
with tab1:

    sign_phase1 = st.selectbox("Select Zodiac", ZODIACS, key="phase1_zodiac_select")

    if "phase1_mode" not in st.session_state:
        st.session_state.phase1_mode = "Daily"

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Daily Prediction", key="btn_daily"):
            st.session_state.phase1_mode = "Daily"
    with col2:
        if st.button("Monthly Prediction", key="btn_monthly"):
            st.session_state.phase1_mode = "Monthly"

    mode = st.session_state.phase1_mode

    # ── DAILY ──────────────────────────────────────────────
    if mode == "Daily":
        data = fetch_daily(sign_phase1)

        if data:
            st.subheader(f"{sign_phase1} Daily Horoscope — {today_str}")

            col_l, col_r = st.columns(2)
            with col_l:
                st.markdown("### General");       st.write(data[0])
                st.markdown("### Career");        st.write(data[1])
                st.markdown("### Love");          st.write(data[2])
            with col_r:
                st.markdown("### Finance");       st.write(data[3])
                st.markdown("### Health");        st.write(data[4])
                color, number = get_daily_lucky(sign_phase1)
                st.success(f"🎨 Lucky Color: {color}")
                st.success(f"🔢 Lucky Number: {number}")

            st.markdown("---")
            st.markdown("### 🪔 Today's Recommended Poojas")
            st.caption(f"Personalised for {sign_phase1} · Updates every day")

            # Use DB poojas if available, else generate dynamically
            if data[7]:
                render_pooja_card(1, {
                    "name"  : data[7],
                    "link"  : data[8],
                    "reason": data[9] or f"Recommended for {sign_phase1} today."
                })
                if data[10]:
                    render_pooja_card(2, {
                        "name"  : data[10],
                        "link"  : data[11],
                        "reason": data[12] or f"Additional blessing for {sign_phase1} today."
                    })
            else:
                # Dynamic — changes every day
                for i, pooja in enumerate(get_daily_poojas(sign_phase1), 1):
                    render_pooja_card(i, pooja)

            st.markdown("---")
            st.markdown("### Daily FAQs")
            for q, a in fetch_daily_faq(sign_phase1):
                with st.expander(q):
                    st.write(a)
        else:
            st.warning("Daily data not found. Run the daily horoscope generator first.")

    # ── MONTHLY ────────────────────────────────────────────
    else:
        data = fetch_monthly(sign_phase1)

        if data:
            st.subheader(f"{sign_phase1} Monthly Horoscope — {month_name} {year}")

            col_l, col_r = st.columns(2)
            with col_l:
                st.markdown("### General");  st.write(data["general"])
                st.markdown("### Love");     st.write(data["love"])
                st.markdown("### Finance");  st.write(data["finance"])
                st.markdown("### Career");   st.write(data["career"])
            with col_r:
                st.markdown("### Business"); st.write(data["business"])
                st.markdown("### Health");   st.write(data["health"])
                st.markdown("### Student");  st.write(data["student"])
                st.markdown("### 🌟 Auspicious Dates")
                st.success(", ".join(format_dates(data["auspicious"])))
                st.markdown("### ⚠️ Inauspicious Dates")
                st.error(", ".join(format_dates(data["inauspicious"])))

            st.markdown("---")
            st.markdown("### 🪔 This Month's Recommended Poojas")
            st.caption(f"Personalised for {sign_phase1} · Updates every month")

            # Two poojas stable all month, change next month
            for i, pooja in enumerate(get_monthly_poojas(sign_phase1), 1):
                render_pooja_card(i, pooja)

            st.markdown("---")
            st.markdown("### Monthly FAQs")
            for q, a in fetch_monthly_faq(sign_phase1):
                with st.expander(q):
                    st.write(a)
        else:
            st.warning("Monthly data not found. Run the monthly predictions generator first.")

# ======================================================
# PHASE 2
# ======================================================
with tab2:

    sign_phase2  = st.selectbox("Select Zodiac for Article", ZODIACS, key="phase2_zodiac_select")
    article      = fetch_article(sign_phase2)
    monthly_data = fetch_monthly(sign_phase2)

    if article:
        st.caption(f"Each section has a unique pooja recommendation for {sign_phase2} — {month_name} {year}")
        display_article(sign_phase2, article)

        if monthly_data:
            st.markdown("---")
            st.subheader(f"{month_name} {year} Key Dates")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("### 🌟 Auspicious Dates")
                st.success(", ".join(format_dates(monthly_data["auspicious"])))
            with col2:
                st.markdown("### ⚠️ Inauspicious Dates")
                st.error(", ".join(format_dates(monthly_data["inauspicious"])))
    else:
        st.warning("No article or monthly data found. Run the predictions generator first.")
        st.info("Run: python monthly_predictions_generator.py")