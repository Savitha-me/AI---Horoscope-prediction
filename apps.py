import streamlit as st
import sqlite3
import json
import hashlib
import re
from datetime import date
import os

# ======================================================
# CONFIG
# ======================================================
DAILY_DB       = "daily_horoscope_prediction.db"
MONTHLY_DB     = "monthly_horoscope.db"
TAMIL_DB       = "monthly_article_tamil.db"
DAILY_FAQ_DB   = "horoscope_faq.db"
MONTHLY_FAQ_DB = "monthly_faq.db"
POOJA_FILE     = "temple_links.json"

ZODIACS = [
    "Aries","Taurus","Gemini","Cancer","Leo","Virgo",
    "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"
]

TAMIL_ZODIACS = [
    "மேஷம்","ரிஷபம்","மிதுனம்","கடகம்","சிம்மம்","கன்னி",
    "துலாம்","விருச்சிகம்","தனுசு","மகரம்","கும்பம்","மீனம்"
]

today      = date.today()
today_str  = str(today)
year       = today.year
month      = today.month
month_name = today.strftime("%B")

# ======================================================
# LOAD ENGLISH POOJAS from temple_links.json
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
# TAMIL POOJA LINKS
# ======================================================
TAMIL_POOJA_MAP = {
    "ஆஸ்ட்ரோவேட் கோயில் சேவைகள்"        : "https://www.astroved.com/temple?promo=SL_MM_AV_Temple",
    "கேது பூஜை"                           : "https://www.astroved.com/temple/kethu-bhagavan-temple/",
    "புதன் பூஜை"                          : "https://www.astroved.com/temple/budhan-bhagavan-temple/",
    "ராகு பூஜை"                           : "https://www.astroved.com/temple/rahu-bhagavan-temple/",
    "குரு பகவான் பூஜை"                    : "https://www.astroved.com/temple/guru-bhagavan-temple/",
    "செவ்வாய் பூஜை"                       : "https://www.astroved.com/temple/chevvai-bhagavan-temple/",
    "சுக்ரன் பூஜை"                        : "https://www.astroved.com/temple/sukra-bhagavan-temple/",
    "சந்திர பூஜை"                         : "https://www.astroved.com/temple/chandra-bhagavan-temple/",
    "சனி பகவான் பூஜை"                     : "https://www.astroved.com/temple/shani-bhagavan-temple/",
    "சூரிய பூஜை"                          : "https://www.astroved.com/temple/surya-bhagavan-temple/",
    "கணபதி பூஜை"                          : "https://www.astroved.com/temple/ganesha-statue/",
    "வியாச திரௌபதி பூஜை"                  : "https://www.astroved.com/temple/vyasa-draupadi/",
    "சிவலிங்க பூஜை"                       : "https://www.astroved.com/temple/shiva-lingam/",
    "நவகிரக பூஜை"                         : "https://www.astroved.com/temple/navagraha/",
    "தன்வந்திரி பூஜை"                     : "https://www.astroved.com/temple/dhanvantri/",
    "நந்தி பூஜை"                          : "https://www.astroved.com/temple/nandi/",
    "வராஹி அம்மன் பூஜை"                   : "https://www.astroved.com/temple/varahi-devi/",
    "பிரத்யங்கிரா பூஜை"                   : "https://www.astroved.com/temple/pratyangira-devi/",
    "லட்சுமி பூஜை"                        : "https://www.astroved.com/temple/lakshmi-devi/",
    "முருகன் பூஜை"                         : "https://www.astroved.com/temple/murugan/",
    "மஹா விஷ்ணு பூஜை"                     : "https://www.astroved.com/temple/maha-vishnu/",
    "அங்காளி அம்மன் பூஜை"                 : "https://www.astroved.com/temple/goddess-angali/",
    "ஸ்ரீம் ப்ரீஸி லட்சுமி பூஜை"          : "https://www.astroved.com/temple/shreem-brzee-lakshmi/",
    "கணேஷ் ஆஞ்சநேய பூஜை"                 : "https://www.astroved.com/temple/ganesha-anjenaya/",
    "சரஸ்வதி பூஜை"                        : "https://www.astroved.com/temple/saraswati/",
    "அகஸ்திய பூஜை"                        : "https://www.astroved.com/temple/agastya-rishi/",
    "பால திரிபுரசுந்தரி பூஜை"             : "https://www.astroved.com/temple/bala-tripura-sundari/",
    "சக்கரதாழ்வார் பூஜை"                  : "https://www.astroved.com/temple/chakrathalwar/",
    "அய்யப்பன் பூஜை"                      : "https://www.astroved.com/temple/ayyappa/",
    "தத்தாத்ரேய ஷீர்டி சாய்பாபா பூஜை"    : "https://www.astroved.com/temple/shirdi-sai-baba/",
    "சித்தி புத்தி கணபதி பூஜை"            : "https://www.astroved.com/temple/siddhi-buddhi-ganapathi/",
    "குபேர பூஜை"                          : "https://www.astroved.com/temple/lord-kuber/",
    "ஹயகிரீவ பூஜை"                        : "https://www.astroved.com/temple/hayagriva/",
    "துர்கை அம்மன் பூஜை"                  : "https://www.astroved.com/temple/maa-durga/",
    "கால பைரவ பூஜை"                       : "https://www.astroved.com/temple/kaala-bhairava/",
    "ஹனுமான் பூஜை"                        : "https://www.astroved.com/temple/hanuman/",
    "ஹேரம்ப கணபதி பூஜை"                   : "https://www.astroved.com/temple/heramba-ganapati/",
    "பால முருகன் பூஜை"                    : "https://www.astroved.com/temple/lord-bala-murugan/",
    "காமதேனு பூஜை"                        : "https://www.astroved.com/temple/kamadhenu-cow/",
    "மஹா மேரு பூஜை"                       : "https://www.astroved.com/temple/maha-meru/",
    "ஹரித்ரா கணபதி பூஜை"                  : "https://www.astroved.com/temple/haridra-ganapati/",
    "க்ஷிப்ர கணபதி பூஜை"                  : "https://www.astroved.com/temple/kshipra-ganapathi/",
    "நரசிம்ம பூஜை"                        : "https://www.astroved.com/temple/narasimha/",
    "கிருஷ்ண பூஜை"                        : "https://www.astroved.com/temple/shri-krishna/",
    "லட்சுமி குபேர பூஜை"                  : "https://www.astroved.com/temple/lakshmi-kuberar/",
    "நடராஜ பூஜை"                          : "https://www.astroved.com/temple/natarajar/",
    "லட்சுமி நாராயண பூஜை"                 : "https://www.astroved.com/temple/lakshmi-narayan/",
    "நால்வர் பூஜை"                        : "https://www.astroved.com/temple/nalvar/",
    "பஞ்சமுகி கணேஷ் பூஜை"                : "https://www.astroved.com/temple/panchamukhi-ganesha/",
    "சரபேஷ்வர பூஜை"                       : "https://www.astroved.com/temple/sharabha/",
}
TAMIL_POOJAS = list(TAMIL_POOJA_MAP.keys())

# ======================================================
# UNIFIED BILINGUAL POOJA POOLS
# Each entry: (english_name, tamil_name, link)
# Both English and Tamil articles pick from the SAME pool
# using the SAME index — guaranteed identical pooja shown.
# Seed = section_key + sign + year + month → rotates monthly.
# ======================================================

UNIFIED_POOJA_POOLS = {
    "overview": [
        ("Saturn Pooja",            "சனி பகவான் பூஜை",          "https://www.astroved.com/temple/shani-bhagavan-temple/"),
        ("Navagraha Pooja",         "நவகிரக பூஜை",              "https://www.astroved.com/temple/navagraha/"),
        ("Maha Vishnu Pooja",       "மஹா விஷ்ணு பூஜை",          "https://www.astroved.com/temple/maha-vishnu/"),
        ("Shiva Lingam Pooja",      "சிவலிங்க பூஜை",            "https://www.astroved.com/temple/shiva-lingam/"),
        ("Nandi Pooja",             "நந்தி பூஜை",               "https://www.astroved.com/temple/nandi/"),
        ("Kala Bhairava Pooja",     "கால பைரவ பூஜை",            "https://www.astroved.com/temple/kaala-bhairava/"),
    ],
    "love": [
        ("Mars Pooja",              "செவ்வாய் பூஜை",            "https://www.astroved.com/temple/chevvai-bhagavan-temple/"),
        ("Venus Pooja",             "சுக்ரன் பூஜை",             "https://www.astroved.com/temple/sukra-bhagavan-temple/"),
        ("Moon Pooja",              "சந்திர பூஜை",              "https://www.astroved.com/temple/chandra-bhagavan-temple/"),
        ("Lakshmi Devi Pooja",      "லட்சுமி பூஜை",             "https://www.astroved.com/temple/lakshmi-devi/"),
        ("Varahi Devi Pooja",       "வராஹி அம்மன் பூஜை",        "https://www.astroved.com/temple/varahi-devi/"),
        ("Vyasa Draupadi Pooja",    "வியாச திரௌபதி பூஜை",       "https://www.astroved.com/temple/vyasa-draupadi/"),
    ],
    "finance": [
        ("Lakshmi Kubera Pooja",         "லட்சுமி குபேர பூஜை",          "https://www.astroved.com/temple/lakshmi-kuberar/"),
        ("Kubera Pooja",                 "குபேர பூஜை",                   "https://www.astroved.com/temple/lord-kuber/"),
        ("Lakshmi Devi Pooja",           "லட்சுமி பூஜை",                 "https://www.astroved.com/temple/lakshmi-devi/"),
        ("Shreem Brzee Lakshmi Pooja",   "ஸ்ரீம் ப்ரீஸி லட்சுமி பூஜை",  "https://www.astroved.com/temple/shreem-brzee-lakshmi/"),
        ("Maha Meru Pooja",              "மஹா மேரு பூஜை",                "https://www.astroved.com/temple/maha-meru/"),
        ("Lakshmi Narayan Pooja",        "லட்சுமி நாராயண பூஜை",          "https://www.astroved.com/temple/lakshmi-narayan/"),
    ],
    "career": [
        ("Moon Pooja",              "சந்திர பூஜை",              "https://www.astroved.com/temple/chandra-bhagavan-temple/"),
        ("Sun Pooja",               "சூரிய பூஜை",               "https://www.astroved.com/temple/surya-bhagavan-temple/"),
        ("Jupiter Pooja",           "குரு பகவான் பூஜை",          "https://www.astroved.com/temple/guru-bhagavan-temple/"),
        ("Saturn Pooja",            "சனி பகவான் பூஜை",          "https://www.astroved.com/temple/shani-bhagavan-temple/"),
        ("Hayagriva Pooja",         "ஹயகிரீவ பூஜை",             "https://www.astroved.com/temple/hayagriva/"),
        ("Murugan Pooja",           "முருகன் பூஜை",              "https://www.astroved.com/temple/murugan/"),
    ],
    "business": [
        ("Mercury Pooja",                    "புதன் பூஜை",               "https://www.astroved.com/temple/budhan-bhagavan-temple/"),
        ("Ganesha Pooja",                    "கணபதி பூஜை",               "https://www.astroved.com/temple/ganesha-statue/"),
        ("Kubera Pooja",                     "குபேர பூஜை",               "https://www.astroved.com/temple/lord-kuber/"),
        ("Lakshmi Kubera Pooja",             "லட்சுமி குபேர பூஜை",       "https://www.astroved.com/temple/lakshmi-kuberar/"),
        ("Ganesha Anjaneya Pooja",           "கணேஷ் ஆஞ்சநேய பூஜை",      "https://www.astroved.com/temple/ganesha-anjenaya/"),
        ("Siddhi Buddhi Ganapathi Pooja",    "சித்தி புத்தி கணபதி பூஜை", "https://www.astroved.com/temple/siddhi-buddhi-ganapathi/"),
    ],
    "health": [
        ("Sun Pooja",               "சூரிய பூஜை",               "https://www.astroved.com/temple/surya-bhagavan-temple/"),
        ("Dhanvantri Pooja",        "தன்வந்திரி பூஜை",           "https://www.astroved.com/temple/dhanvantri/"),
        ("Mars Pooja",              "செவ்வாய் பூஜை",             "https://www.astroved.com/temple/chevvai-bhagavan-temple/"),
        ("Maa Durga Pooja",         "துர்கை அம்மன் பூஜை",        "https://www.astroved.com/temple/maa-durga/"),
        ("Narasimha Pooja",         "நரசிம்ம பூஜை",              "https://www.astroved.com/temple/narasimha/"),
        ("Pratyangira Devi Pooja",  "பிரத்யங்கிரா பூஜை",         "https://www.astroved.com/temple/pratyangira-devi/"),
    ],
    "education": [
        ("Saraswati Pooja",         "சரஸ்வதி பூஜை",             "https://www.astroved.com/temple/saraswati/"),
        ("Hayagriva Pooja",         "ஹயகிரீவ பூஜை",             "https://www.astroved.com/temple/hayagriva/"),
        ("Mercury Pooja",           "புதன் பூஜை",               "https://www.astroved.com/temple/budhan-bhagavan-temple/"),
        ("Jupiter Pooja",           "குரு பகவான் பூஜை",          "https://www.astroved.com/temple/guru-bhagavan-temple/"),
        ("Murugan Pooja",           "முருகன் பூஜை",              "https://www.astroved.com/temple/murugan/"),
        ("Kshipra Ganapathi Pooja", "க்ஷிப்ர கணபதி பூஜை",       "https://www.astroved.com/temple/kshipra-ganapathi/"),
    ],
}

# Tamil zodiac → English zodiac (used to normalise the seed so EN & TA pick identical index)
TAMIL_TO_ENGLISH_SIGN = {
    "மேஷம்":"Aries","ரிஷபம்":"Taurus","மிதுனம்":"Gemini","கடகம்":"Cancer",
    "சிம்மம்":"Leo","கன்னி":"Virgo","துலாம்":"Libra","விருச்சிகம்":"Scorpio",
    "தனுசு":"Sagittarius","மகரம்":"Capricorn","கும்பம்":"Aquarius","மீனம்":"Pisces",
}

def _english_sign(sign):
    """Return the English sign name regardless of whether sign is EN or TA."""
    return TAMIL_TO_ENGLISH_SIGN.get(sign, sign)

# Section heading → pool key
# Uses ordered list so longer / more-specific Tamil phrases are checked first
# to avoid partial-match collisions (e.g. "நிலை" inside "ஒட்டுமொத்த நிலை").
SECTION_KEYWORD_LIST = [
    # ── English (lowercase keywords) ───────────────────
    ("overview",      "overview"),
    ("general",       "overview"),
    ("love",          "love"),
    ("relationship",  "love"),
    ("finance",       "finance"),
    ("wealth",        "finance"),
    ("career",        "career"),
    ("professional",  "career"),
    ("business",      "business"),
    ("health",        "health"),
    ("wellness",      "health"),
    ("education",     "education"),
    ("learning",      "education"),
    ("student",       "education"),
    # ── Tamil (exact substrings as they appear in headings) ─
    ("ஒட்டுமொத்த நிலை",              "overview"),
    ("ஒட்டுமொத்த",                   "overview"),
    ("காதல் மற்றும் உறவுகள்",         "love"),
    ("காதல்",                         "love"),
    ("உறவுகள்",                       "love"),
    ("பணம் மற்றும் செல்வம்",          "finance"),
    ("நிதி நிலை",                     "finance"),
    ("நிதி",                          "finance"),
    ("பணம்",                          "finance"),
    ("செல்வம்",                       "finance"),
    ("தொழில் மற்றும் வேலை முன்னேற்றம்", "career"),
    ("தொழில் வளர்ச்சி",               "career"),
    ("தொழில்",                        "career"),
    ("வேலை முன்னேற்றம்",              "career"),
    ("வேலை",                          "career"),
    ("வியாபார வளர்ச்சி",              "business"),
    ("வியாபாரம்",                     "business"),
    ("வியாபார",                       "business"),
    ("உடல் நலம்",                     "health"),
    ("உடல் ஆரோக்கியம்",               "health"),
    ("ஆரோக்கியம்",                    "health"),
    ("உடல்",                          "health"),
    ("கல்வி மற்றும் மாணவர்கள்",       "education"),
    ("கல்வி",                         "education"),
    ("மாணவர்கள்",                     "education"),
    ("மாணவர்",                        "education"),
]

def _resolve_pool_key(section):
    """
    Map any section heading (English or Tamil) to a pool key.
    Checks longer phrases first to avoid partial-match errors.
    """
    s  = section.strip()
    sl = s.lower()          # for English case-insensitive match
    for kw, pool_key in SECTION_KEYWORD_LIST:
        if kw in sl or kw in s:
            return pool_key
    return "overview"       # safe default

def _pick_entry(pool_key, sign):
    """
    Pick one entry from the unified pool deterministically.
    Seed always uses the ENGLISH sign name so Tamil and English
    articles produce the exact same index for the same zodiac.
    Seed = pool_key | english_sign | year | month  → rotates monthly.
    Returns (english_name, tamil_name, link).
    """
    pool        = UNIFIED_POOJA_POOLS.get(pool_key, UNIFIED_POOJA_POOLS["overview"])
    en_sign     = _english_sign(sign)          # ← key fix: normalise to English
    seed        = f"{pool_key}|{en_sign}|{year}|{month}"
    h           = hashlib.md5(seed.encode()).hexdigest()
    idx         = int(h[:4], 16) % len(pool)
    return pool[idx]                            # (en_name, ta_name, link)

def get_dynamic_pooja(sign, section):
    """English article: returns (english_name, link)."""
    pool_key         = _resolve_pool_key(section)
    en_name, _, link = _pick_entry(pool_key, sign)
    return en_name, link

def get_section_pooja_tamil(sign, section):
    """Tamil article: returns (tamil_name, link) — guaranteed same entry as English."""
    pool_key          = _resolve_pool_key(section)
    _, ta_name, link  = _pick_entry(pool_key, sign)
    return ta_name, link

# ======================================================
# DAILY LUCKY
# ======================================================
def get_daily_lucky(sign):
    h = hashlib.md5((sign + today_str).encode()).hexdigest()
    colors = [
        "Red","Blue","Green","Yellow","White",
        "Pink","Orange","Purple","Brown","Grey","Gold","Silver"
    ]
    color_index  = int(h[:2], 16) % len(colors)
    lucky_number = (int(h[2:6], 16) % 9) + 1
    return colors[color_index], lucky_number

# ======================================================
# WORD COUNT & AUTO EXPAND
# ======================================================
def count_words(text):
    return len(text.split())

def expand_article_to_min_words(text, min_words=900):
    if count_words(text) >= min_words:
        return text

    def extra_paragraph(section):
        return (
            f"This month brings gradual developments in the area of {section.lower()}. "
            f"Consistent effort, patience, and a balanced approach will help you achieve steady progress. "
            f"Avoid impulsive decisions and focus on long-term stability. "
            f"Positive planetary influences may open new opportunities, but careful planning will be essential. "
            f"Maintaining emotional balance and practical thinking will help you make the most of this period."
        )

    lines = text.split("\n")
    expanded = []
    for line in lines:
        expanded.append(line)
        s = line.strip()
        if s.startswith("Heading 2:"):
            section = s.replace("Heading 2:", "").strip()
            expanded.append("")
            expanded.append(extra_paragraph(section))
            expanded.append("")

    expanded_text = "\n".join(expanded)
    if count_words(expanded_text) < min_words:
        expanded_text += "\n\n" + extra_paragraph("overall growth and stability")
    return expanded_text

# ======================================================
# DATABASE — DAILY
# ======================================================
def fetch_daily(sign):
    if not os.path.exists(DAILY_DB):
        return None
    conn = None
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
        return cur.fetchone()
    except Exception as e:
        st.error(f"Daily DB error: {e}")
        return None
    finally:
        if conn: conn.close()

# ======================================================
# DATABASE — MONTHLY SHORT PREDICTIONS
# ======================================================
def fetch_monthly(sign):
    if not os.path.exists(MONTHLY_DB):
        return None
    conn = None
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
        if not row:
            return None
        return {
            "general"     : row[0], "love"        : row[1],
            "finance"     : row[2], "career"      : row[3],
            "business"    : row[4], "health"      : row[5],
            "student"     : row[6],
            "auspicious"  : json.loads(row[7]),
            "inauspicious": json.loads(row[8]),
        }
    except Exception as e:
        st.error(f"Monthly DB error: {e}")
        return None
    finally:
        if conn: conn.close()

# ======================================================
# DATABASE — ENGLISH ARTICLE
# ======================================================
def fetch_article(sign):
    if not os.path.exists(MONTHLY_DB):
        return None
    conn         = None
    article_text = None
    try:
        conn = sqlite3.connect(MONTHLY_DB)
        cur  = conn.cursor()
        cur.execute("PRAGMA table_info(monthly_horoscope)")
        cols = [c[1] for c in cur.fetchall()]
        if not cols:
            return None

        if "article_text" in cols:
            cur.execute("""
                SELECT article_text FROM monthly_horoscope
                WHERE zodiac_sign=? AND year=? AND month=?
            """, (sign, year, month))
            row = cur.fetchone()
            if row and row[0] and row[0].strip():
                article_text = row[0]

        if not article_text:
            cur.execute("""
                SELECT general, love, finance, career, business, health, student
                FROM monthly_horoscope
                WHERE zodiac_sign=? AND year=? AND month=?
            """, (sign, year, month))
            row = cur.fetchone()
            if row:
                def clean(t):
                    if not t: return ""
                    return "\n".join(
                        l for l in t.split("\n")
                        if not l.strip().lower().startswith("divine technique")
                        and not l.strip().lower().startswith("remedy:")
                    ).strip()

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
                    if content: built.append(content)
                    built.append("")
                article_text = "\n".join(built)
    except Exception as e:
        st.error(f"Article fetch error: {e}")
    finally:
        if conn: conn.close()
    return article_text

# ======================================================
# DATABASE — TAMIL ARTICLE
# ======================================================
def fetch_tamil_article(sign):
    if not os.path.exists(TAMIL_DB):
        return None, None, None
    conn = None
    try:
        conn = sqlite3.connect(TAMIL_DB)
        cur  = conn.cursor()
        cur.execute("""
            SELECT article_text, year, month
            FROM monthly_articles_tamil
            WHERE zodiac_sign=?
            ORDER BY year DESC, month DESC
            LIMIT 1
        """, (sign,))
        row = cur.fetchone()
        if row:
            return row[0], row[1], row[2]
        return None, None, None
    except Exception as e:
        st.error(f"Tamil DB error: {e}")
        return None, None, None
    finally:
        if conn: conn.close()

# ======================================================
# FAQs
# ======================================================
def fetch_daily_faq(sign):
    if not os.path.exists(DAILY_FAQ_DB): return []
    conn = None
    try:
        conn = sqlite3.connect(DAILY_FAQ_DB)
        cur  = conn.cursor()
        cur.execute("SELECT question, answer FROM daily_faq WHERE moon_sign=? AND date=?", (sign, today_str))
        return cur.fetchall()
    except: return []
    finally:
        if conn: conn.close()

def fetch_monthly_faq(sign):
    if not os.path.exists(MONTHLY_FAQ_DB): return []
    conn = None
    try:
        conn = sqlite3.connect(MONTHLY_FAQ_DB)
        cur  = conn.cursor()
        cur.execute("SELECT question, answer FROM monthly_faq WHERE moon_sign=? AND month=?", (sign, f"{year}-{month:02d}"))
        return cur.fetchall()
    except: return []
    finally:
        if conn: conn.close()

# ======================================================
# DISPLAY ENGLISH ARTICLE (Phase 2)
# ======================================================
H2_KEYWORDS = [
    "overview","love","relationship","career","business",
    "finance","wealth","health","wellness","education",
    "learning","student","key dates","lucky","advice"
]

def is_bold_h2(s):
    m = re.match(r'^\*\*(.+)\*\*$', s)
    if m:
        return any(kw in m.group(1).lower() for kw in H2_KEYWORDS)
    return False

def is_bold_h3(s):
    m = re.match(r'^\*\*(.+)\*\*$', s)
    if m:
        return not any(kw in m.group(1).lower() for kw in H2_KEYWORDS)
    return False

def display_article(sign, text):
    lines           = text.split("\n")
    current_section = ""
    section_buffer  = []

    def flush_section():
        for ln in section_buffer:
            s = ln.strip()
            if not s:
                continue
            if s.lower().startswith("divine technique") or s.lower().startswith("remedy:"):
                continue
            if s.startswith("Heading 3:"):
                st.markdown(f"### {s.replace('Heading 3:', '').strip()}")
            elif is_bold_h3(s):
                st.markdown(s)
            else:
                st.write(s)

        if current_section:
            name, link = get_dynamic_pooja(sign, current_section)
            st.markdown(
                f"🪔 *Divine technique to improve your {current_section}:* "
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
            if current_section:
                flush_section()
            current_section = s.replace("Heading 2:", "").strip()
            st.markdown(f"## {current_section}")

        elif is_bold_h2(s):
            if current_section:
                flush_section()
            current_section = re.match(r'^\*\*(.+)\*\*$', s).group(1)
            st.markdown(f"## {current_section}")

        else:
            section_buffer.append(line)

    if current_section:
        flush_section()

# ======================================================
# DISPLAY TAMIL ARTICLE (Phase 3)
# ======================================================
def display_tamil_article(sign, text):
    import re as _re

    lines           = text.split("\n")
    current_section = ""
    section_buffer  = []
    content_found   = False

    # Regex to detect and remove non-Tamil/non-ASCII foreign scripts (e.g. Chinese 方面)
    _foreign_script_re = _re.compile(
        r'[\u4e00-\u9fff'       # CJK Unified Ideographs (Chinese/Japanese/Korean)
        r'\u3040-\u30ff'        # Hiragana / Katakana
        r'\uac00-\ud7af'        # Korean Hangul syllables
        r'\u0600-\u06ff'        # Arabic
        r'\u0900-\u097f]'       # Devanagari
    )

    def _clean_line(s):
        """
        Remove:
        - Prompt echo lines: 'ராசி: ...', 'பிரிவு: ...'
        - Lines that are entirely foreign script characters (e.g. Chinese)
        - Inline foreign script words
        """
        # Strip prompt echo headers (case-insensitive prefix match)
        lower = s.lower()
        if lower.startswith("ராசி:") or lower.startswith("பிரிவு:"):
            return None
        if lower.startswith("rasi:") or lower.startswith("piriv"):
            return None
        # Remove foreign-script characters inline
        cleaned = _foreign_script_re.sub("", s).strip()
        # If the line becomes empty after stripping foreign chars, skip it
        if not cleaned:
            return None
        return cleaned

    def flush_section():
        nonlocal content_found
        if not section_buffer:
            return
        content_found = True

        for ln in section_buffer:
            s = ln.strip()
            if not s:
                continue
            if s.lower().startswith("divine technique") or s.lower().startswith("remedy:"):
                continue
            s = _clean_line(s)
            if s is None:
                continue
            if s.startswith("Heading 3:"):
                st.markdown(f"### {s.replace('Heading 3:', '').strip()}")
            else:
                st.markdown(s)

        if current_section:
            name, link = get_section_pooja_tamil(sign, current_section)
            st.markdown(
                f"🪔 *உங்கள் {current_section} மேம்படுத்த தெய்வீக வழி:* "
                f"**[{name}]({link})**"
            )
        section_buffer.clear()

    for line in lines:
        s = line.strip()
        if not s:
            continue

        if _re.match(r'^# [^#]', s):
            flush_section()
            st.markdown(s)

        elif _re.match(r'^## [^#]', s):
            flush_section()
            current_section = _re.sub(r'^##\s*', '', s).strip()
            st.markdown(f"## {current_section}")

        elif s.startswith("Heading 1:"):
            flush_section()
            st.markdown(f"# {s.replace('Heading 1:', '').strip()}")

        elif s.startswith("Heading 2:"):
            flush_section()
            current_section = s.replace("Heading 2:", "").strip()
            st.markdown(f"## {current_section}")

        else:
            section_buffer.append(line)

    flush_section()

    if not content_found:
        st.warning("Heading format not detected. Showing full article.")
        st.write(text)

# ======================================================
# META TITLE & DESCRIPTION HELPERS
# Target: Title 50-60 chars, Description 150-160 chars
# ======================================================
def build_meta_english(sign, month_name, year):
    """Build English meta title (50-60 chars) and description (150-160 chars)."""
    # Try variations to land in 50-60 char range
    candidates_title = [
        f"{sign} Monthly Horoscope {month_name} {year}",
        f"{sign} Horoscope {month_name} {year} Predictions",
        f"{sign} Monthly Horoscope – {month_name} {year}",
    ]
    meta_title = candidates_title[0]
    for c in candidates_title:
        if 50 <= len(c) <= 60:
            meta_title = c
            break
    # Clamp if still out of range
    if len(meta_title) > 60:
        meta_title = meta_title[:60]

    # Description — target 150-160 chars
    candidates_desc = [
        f"Read {sign} monthly horoscope for {month_name} {year}. Predictions for love, career, finance, health & divine remedies to enhance your month.",
        f"Explore {sign} horoscope for {month_name} {year}. Accurate forecasts for love, career, finance, health & powerful pooja remedies for a great month.",
        f"Get {sign} monthly horoscope {month_name} {year}. Love, career, finance & health predictions with divine remedy tips to make the most of your month.",
    ]
    meta_desc = candidates_desc[0]
    for c in candidates_desc:
        if 150 <= len(c) <= 160:
            meta_desc = c
            break
    # Clamp if needed
    if len(meta_desc) > 160:
        meta_desc = meta_desc[:157] + "..."
    return meta_title, meta_desc


def build_meta_tamil(sign_tamil, month_name_tamil, year):
    """Build Tamil meta title (50-60 chars) and description (150-160 chars)."""
    candidates_title = [
        f"{sign_tamil} மாத ராசிபலன் {month_name_tamil} {year}",
        f"{sign_tamil} ராசிபலன் {month_name_tamil} {year} – முழு பலன்கள்",
        f"{sign_tamil} மாத ஜோதிடம் {month_name_tamil} {year}",
    ]
    meta_title = candidates_title[0]
    for c in candidates_title:
        if 50 <= len(c) <= 60:
            meta_title = c
            break
    if len(meta_title) > 60:
        meta_title = meta_title[:60]

    candidates_desc = [
        f"{sign_tamil} ராசிக்கு {month_name_tamil} {year} மாத விரிவான பலன்கள். காதல், தொழில், பணம், உடல் நலம் மற்றும் தெய்வீக பூஜை பரிந்துரைகள் பெறுங்கள்.",
        f"{sign_tamil} {month_name_tamil} {year} ராசிபலன் – காதல், தொழில், நிதி, ஆரோக்கியம் மற்றும் சிறந்த பூஜை தீர்வுகளுடன் விரிவான மாத கணிப்புகள் இங்கே.",
        f"{sign_tamil} மாத ராசிபலன் {month_name_tamil} {year}: காதல், தொழில், பணம் & உடல் நலம் பலன்கள் மற்றும் தெய்வீக தீர்வுகள் அறிந்துகொள்ளுங்கள்.",
    ]
    meta_desc = candidates_desc[0]
    for c in candidates_desc:
        if 150 <= len(c) <= 160:
            meta_desc = c
            break
    if len(meta_desc) > 160:
        meta_desc = meta_desc[:157] + "..."
    return meta_title, meta_desc


# ======================================================
# UI — 3 TABS
# ======================================================
st.set_page_config(layout="wide", page_title="AI Horoscope Portal")
st.title("🔮 AI Horoscope Portal")

tab1, tab2, tab3 = st.tabs([
    "Phase 1 : Predictions",
    "Phase 2 : English Articles",
    "Phase 3 : Tamil Articles"
])

# ======================================================
# PHASE 1 — Daily & Monthly Predictions
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

    # ── DAILY ──────────────────────────────────────────
    if mode == "Daily":
        data = fetch_daily(sign_phase1)

        if data:
            st.subheader(f"{sign_phase1} Daily Horoscope — {today_str}")

            st.markdown("### General");  st.write(data[0])
            st.markdown("### Career");   st.write(data[1])
            st.markdown("### Love");     st.write(data[2])
            st.markdown("### Finance");  st.write(data[3])
            st.markdown("### Health");   st.write(data[4])

            color, number = get_daily_lucky(sign_phase1)
            st.success(f"Lucky Color: {color}")
            st.success(f"Lucky Number: {number}")

            st.markdown("### 🪔 Recommended Poojas")
            if data[7]:
                st.markdown(f"**[{data[7]}]({data[8]})**")
                st.caption(data[9])
            if data[10]:
                st.markdown(f"**[{data[10]}]({data[11]})**")
                st.caption(data[12])

            st.markdown("---")
            st.markdown("### Daily FAQs")
            for q, a in fetch_daily_faq(sign_phase1):
                with st.expander(q):
                    st.write(a)
        else:
            st.warning("Daily data not found")

    # ── MONTHLY ────────────────────────────────────────
    else:
        data = fetch_monthly(sign_phase1)

        if data:
            st.subheader(f"{sign_phase1} Monthly Horoscope — {month_name}")

            for k, v in data.items():
                if k not in ["auspicious", "inauspicious"]:
                    st.markdown(f"### {k.title()}")
                    st.write(v)

            st.markdown("### 🌟 Auspicious Dates")
            st.success(", ".join(map(str, data["auspicious"])))

            st.markdown("### ⚠️ Inauspicious Dates")
            st.error(", ".join(map(str, data["inauspicious"])))

            st.markdown("---")
            st.markdown("### Monthly FAQs")
            for q, a in fetch_monthly_faq(sign_phase1):
                with st.expander(q):
                    st.write(a)
        else:
            st.warning("Monthly data not found")

# ======================================================
# PHASE 2 — English Monthly Article
# ======================================================
with tab2:

    sign_phase2  = st.selectbox("Select Zodiac for Article", ZODIACS, key="phase2_zodiac_select")
    article      = fetch_article(sign_phase2)
    monthly_data = fetch_monthly(sign_phase2)

    if article:
        article = expand_article_to_min_words(article, min_words=900)
        st.caption(f"Total words: {count_words(article)} | {month_name} {year}")

        # ── Meta Title & Description (inline, no expander) ──
        meta_title_en, meta_desc_en = build_meta_english(sign_phase2, month_name, year)

        st.markdown("**Meta Title:**")
        st.code(meta_title_en, language=None)
        st.markdown("**Meta Description:**")
        st.code(meta_desc_en, language=None)
        st.markdown("---")

        display_article(sign_phase2, article)

        if monthly_data:
            st.markdown("---")
            st.subheader(f"{month_name} {year} Key Dates")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("### 🌟 Auspicious Dates")
                st.success(", ".join(map(str, monthly_data["auspicious"])))
            with col2:
                st.markdown("### ⚠️ Inauspicious Dates")
                st.error(", ".join(map(str, monthly_data["inauspicious"])))
    else:
        st.warning("Monthly article not generated yet.")

# ======================================================
# PHASE 3 — Tamil Monthly Article
# ======================================================

TAMIL_TO_ENGLISH_ZODIAC = {
    "மேஷம்"      : "Aries",
    "ரிஷபம்"     : "Taurus",
    "மிதுனம்"    : "Gemini",
    "கடகம்"      : "Cancer",
    "சிம்மம்"    : "Leo",
    "கன்னி"      : "Virgo",
    "துலாம்"     : "Libra",
    "விருச்சிகம்": "Scorpio",
    "தனுசு"      : "Sagittarius",
    "மகரம்"      : "Capricorn",
    "கும்பம்"    : "Aquarius",
    "மீனம்"      : "Pisces",
}

TAMIL_MONTHS = {
    1:"ஜனவரி", 2:"பிப்ரவரி", 3:"மார்ச்", 4:"ஏப்ரல்",
    5:"மே", 6:"ஜூன்", 7:"ஜூலை", 8:"ஆகஸ்ட்",
    9:"செப்டம்பர்", 10:"அக்டோபர்", 11:"நவம்பர்", 12:"டிசம்பர்"
}

with tab3:

    st.subheader("🔮 தமிழ் மாத ஜோதிட கட்டுரை")

    sign_phase3 = st.selectbox(
        "ராசியை தேர்வு செய்யவும் (Select Zodiac)",
        TAMIL_ZODIACS,
        key="phase3_zodiac_select"
    )

    tamil_article, art_year, art_month = fetch_tamil_article(sign_phase3)

    english_sign_phase3  = TAMIL_TO_ENGLISH_ZODIAC.get(sign_phase3, sign_phase3)
    tamil_monthly_data   = fetch_monthly(english_sign_phase3)

    if tamil_article:
        # Replace any English month name in the H1 title with Tamil equivalent
        # (fixes articles generated before this patch)
        for en_m, ta_m in [
            ("January","ஜனவரி"),("February","பிப்ரவரி"),("March","மார்ச்"),
            ("April","ஏப்ரல்"),("May","மே"),("June","ஜூன்"),
            ("July","ஜூலை"),("August","ஆகஸ்ட்"),("September","செப்டம்பர்"),
            ("October","அக்டோபர்"),("November","நவம்பர்"),("December","டிசம்பர்")
        ]:
            tamil_article = tamil_article.replace(
                f"ராசிபலன் - {en_m}",
                f"ராசிபலன் - {ta_m}"
            )

        ta_art_month_name = TAMIL_MONTHS.get(art_month, str(art_month))
        st.caption(f"{sign_phase3} – {ta_art_month_name} {art_year}")
        words = count_words(tamil_article)
        st.info(f"மொத்த வார்த்தைகள் (Total Words): {words}")
        if words < 800:
            st.warning("Article length is below expected (800+ words).")

        # ── Meta Title & Description (inline, no expander) ──
        tamil_month_meta = TAMIL_MONTHS.get(month, month_name)
        meta_title_ta, meta_desc_ta = build_meta_tamil(sign_phase3, tamil_month_meta, year)

        st.markdown("**மெட்டா தலைப்பு (Meta Title):**")
        st.code(meta_title_ta, language=None)
        st.markdown("**மெட்டா விவரம் (Meta Description):**")
        st.code(meta_desc_ta, language=None)
        st.markdown("---")

        display_tamil_article(sign_phase3, tamil_article)

        if tamil_monthly_data:
            tamil_month_name = TAMIL_MONTHS.get(month, month_name)
            st.markdown("---")
            st.subheader(f"{tamil_month_name} {year} முக்கிய தேதிகள்")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("### 🌟 சுப தேதிகள்")
                st.success(", ".join(map(str, tamil_monthly_data["auspicious"])))
            with col2:
                st.markdown("### ⚠️ அசுப தேதிகள்")
                st.error(", ".join(map(str, tamil_monthly_data["inauspicious"])))
    else:
        st.error("Tamil article not found.")
        st.info("Run: python monthly_article_tamil_generator.py")