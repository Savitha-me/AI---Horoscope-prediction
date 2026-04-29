from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import json
from datetime import date

app = FastAPI(
    title="Horoscope API",
    description="Daily & Monthly horoscope predictions, FAQs, and Tamil articles",
    version="1.0.0"
)

# ===============================
# CORS — allow all origins
# (restrict in production if needed)
# ===============================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===============================
# Constants
# ===============================
ZODIACS = [
    "aries", "taurus", "gemini", "cancer", "leo", "virgo",
    "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"
]

ZODIACS_TAMIL = [
    "மேஷம்", "ரிஷபம்", "மிதுனம்", "கடகம்", "சிம்மம்", "கன்னி",
    "துலாம்", "விருச்சிகம்", "தனுசு", "மகரம்", "கும்பம்", "மீனம்"
]

EN_TO_TAMIL = {e.lower(): t for e, t in zip(
    ["Aries","Taurus","Gemini","Cancer","Leo","Virgo",
     "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"],
    ZODIACS_TAMIL
)}

# ===============================
# DB file paths
# ===============================
DAILY_DB        = "daily_horoscope_prediction.db"
MONTHLY_DB      = "monthly_horoscope.db"
DAILY_FAQ_DB    = "horoscope_faq.db"
MONTHLY_FAQ_DB  = "monthly_faq.db"
TAMIL_DB        = "monthly_article_tamil.db"


# ===============================
# Helper — DB connection
# ===============================
def get_conn(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row   # lets us access columns by name
    return conn


def validate_sign(sign: str):
    if sign.lower() not in ZODIACS:
        raise HTTPException(
            status_code=404,
            detail=f"'{sign}' is not a valid zodiac sign. "
                   f"Valid signs: {', '.join(ZODIACS)}"
        )
    return sign.capitalize()


# ================================================
# ROOT
# ================================================
@app.get("/")
def root():
    return {
        "message"        : "Horoscope API is running 🔮",
        "available_signs": ZODIACS,
        "endpoints": {
            "daily_prediction" : "/horoscope/{sign}/daily",
            "monthly_prediction": "/horoscope/{sign}/monthly",
            "daily_faq"        : "/faq/{sign}/daily",
            "monthly_faq"      : "/faq/{sign}/monthly",
            "tamil_article"    : "/articles/tamil/{sign}",
        }
    }


# ================================================
# 1. DAILY HOROSCOPE  (predictions + lucky + poojas + FAQs)
#    Reads from: daily_horoscope_prediction.db + horoscope_faq.db
# ================================================
@app.get("/horoscope/{sign}/daily")
def daily_horoscope(sign: str):
    sign_cap = validate_sign(sign)
    today    = str(date.today())

    # ── Predictions ──────────────────────────────
    conn   = get_conn(DAILY_DB)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT general, career, love, finance, health,
               lucky_color, lucky_number,
               pooja_1_name, pooja_1_link, pooja_1_reason,
               pooja_2_name, pooja_2_link, pooja_2_reason
        FROM daily_horoscope
        WHERE date = ? AND zodiac_sign = ?
    """, (today, sign_cap))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(
            status_code=404,
            detail=f"No daily prediction found for {sign_cap} on {today}. "
                   "Please run the daily generator script first."
        )

    # ── FAQs (from horoscope_faq.db) ─────────────
    faq_conn   = get_conn(DAILY_FAQ_DB)
    faq_cursor = faq_conn.cursor()
    faq_cursor.execute("""
        SELECT question, answer
        FROM daily_faq
        WHERE date = ? AND moon_sign = ?
        ORDER BY id
    """, (today, sign_cap))
    faq_rows = faq_cursor.fetchall()
    faq_conn.close()

    return {
        "sign" : sign_cap,
        "type" : "daily",
        "date" : today,

        "predictions": {
            "general" : row["general"],
            "career"  : row["career"],
            "love"    : row["love"],
            "finance" : row["finance"],
            "health"  : row["health"],
        },

        "lucky": {
            "color" : row["lucky_color"],
            "number": row["lucky_number"],
        },

        "poojas": [
            {
                "name"  : row["pooja_1_name"],
                "link"  : row["pooja_1_link"],
                "reason": row["pooja_1_reason"],
            },
            {
                "name"  : row["pooja_2_name"],
                "link"  : row["pooja_2_link"],
                "reason": row["pooja_2_reason"],
            },
        ],

        # FAQs included — empty list if generator hasn't run yet
        "faqs": [
            {"question": r["question"], "answer": r["answer"]}
            for r in faq_rows
        ]
    }


# ================================================
# 2. MONTHLY HOROSCOPE  (predictions + dates + FAQs)
#    Reads from: monthly_horoscope.db + monthly_faq.db
# ================================================
@app.get("/horoscope/{sign}/monthly")
def monthly_horoscope(sign: str):
    sign_cap      = validate_sign(sign)
    today         = date.today()
    year          = today.year
    month         = today.month
    current_month = today.strftime("%Y-%m")

    # ── Predictions ──────────────────────────────
    conn   = get_conn(MONTHLY_DB)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT general, love, finance, career, business, health, student,
               auspicious_dates, inauspicious_dates
        FROM monthly_horoscope
        WHERE year = ? AND month = ? AND zodiac_sign = ?
    """, (year, month, sign_cap))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(
            status_code=404,
            detail=f"No monthly prediction found for {sign_cap} ({month}/{year}). "
                   "Please run the monthly generator script first."
        )

    try:
        auspicious   = json.loads(row["auspicious_dates"] or "[]")
        inauspicious = json.loads(row["inauspicious_dates"] or "[]")
    except Exception:
        auspicious   = []
        inauspicious = []

    # ── FAQs (from monthly_faq.db) ───────────────
    faq_conn   = get_conn(MONTHLY_FAQ_DB)
    faq_cursor = faq_conn.cursor()
    faq_cursor.execute("""
        SELECT question, answer
        FROM monthly_faq
        WHERE month = ? AND moon_sign = ?
        ORDER BY id
    """, (current_month, sign_cap))
    faq_rows = faq_cursor.fetchall()
    faq_conn.close()

    return {
        "sign" : sign_cap,
        "type" : "monthly",
        "month": today.strftime("%B %Y"),

        "predictions": {
            "general"  : row["general"],
            "love"     : row["love"],
            "finance"  : row["finance"],
            "career"   : row["career"],
            "business" : row["business"],
            "health"   : row["health"],
            "student"  : row["student"],
        },

        "auspicious_dates"  : auspicious,
        "inauspicious_dates": inauspicious,

        # FAQs included — empty list if generator hasn't run yet
        "faqs": [
            {"question": r["question"], "answer": r["answer"]}
            for r in faq_rows
        ]
    }


# ================================================
# 3. DAILY FAQ
#    Reads from: horoscope_faq.db  →  daily_faq table
# ================================================
@app.get("/faq/{sign}/daily")
def daily_faq(sign: str):
    sign_cap = validate_sign(sign)
    today    = str(date.today())

    conn   = get_conn(DAILY_FAQ_DB)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT question, answer
        FROM daily_faq
        WHERE date = ? AND moon_sign = ?
        ORDER BY id
    """, (today, sign_cap))

    rows = cursor.fetchall()
    conn.close()

    if not rows:
        raise HTTPException(
            status_code=404,
            detail=f"No daily FAQs found for {sign_cap} on {today}. "
                   "Please run the daily FAQ generator script first."
        )

    return {
        "sign": sign_cap,
        "type": "daily_faq",
        "date": today,
        "faqs": [{"question": r["question"], "answer": r["answer"]} for r in rows]
    }


# ================================================
# 4. MONTHLY FAQ
#    Reads from: monthly_faq.db  →  monthly_faq table
# ================================================
@app.get("/faq/{sign}/monthly")
def monthly_faq(sign: str):
    sign_cap     = validate_sign(sign)
    current_month = date.today().strftime("%Y-%m")

    conn   = get_conn(MONTHLY_FAQ_DB)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT question, answer
        FROM monthly_faq
        WHERE month = ? AND moon_sign = ?
        ORDER BY id
    """, (current_month, sign_cap))

    rows = cursor.fetchall()
    conn.close()

    if not rows:
        raise HTTPException(
            status_code=404,
            detail=f"No monthly FAQs found for {sign_cap} ({current_month}). "
                   "Please run the monthly FAQ generator script first."
        )

    return {
        "sign" : sign_cap,
        "type" : "monthly_faq",
        "month": date.today().strftime("%B %Y"),
        "faqs" : [{"question": r["question"], "answer": r["answer"]} for r in rows]
    }


# ================================================
# 5. TAMIL MONTHLY ARTICLE
#    Reads from: monthly_article_tamil.db
# ================================================
# ── This function MUST come BEFORE the tamil_article endpoint ──

def parse_tamil_article(raw_text: str) -> dict:
    title           = ""
    sections        = []
    current_heading = None
    current_lines   = []

    for line in raw_text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("Heading 1:"):
            title = line.replace("Heading 1:", "").strip()
        elif line.startswith("Heading 2:"):
            if current_heading is not None:
                sections.append({
                    "heading": current_heading,
                    "content": " ".join(current_lines).strip()
                })
            current_heading = line.replace("Heading 2:", "").strip()
            current_lines   = []
        else:
            if current_heading is not None:
                current_lines.append(line)

    if current_heading is not None:
        sections.append({
            "heading": current_heading,
            "content": " ".join(current_lines).strip()
        })

    return {"title": title, "sections": sections}

@app.get("/articles/tamil/{sign}")
def tamil_article(sign: str):
    sign_cap   = validate_sign(sign)
    tamil_sign = EN_TO_TAMIL.get(sign.lower())
    today      = date.today()
    year       = today.year
    month      = today.month
 
    conn   = get_conn(TAMIL_DB)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT article_text
        FROM monthly_articles_tamil
        WHERE year = ? AND month = ? AND zodiac_sign = ?
    """, (year, month, tamil_sign))
    row = cursor.fetchone()
    conn.close()



    if not row:
        raise HTTPException(
            status_code=404,
            detail=f"No Tamil article found for {sign_cap} ({month}/{year}). "
               "Please run the Tamil article generator script first."
    )

    m_conn   = get_conn(MONTHLY_DB)
    m_cursor = m_conn.cursor()
    m_cursor.execute("""
        SELECT auspicious_dates, inauspicious_dates
        FROM monthly_horoscope
        WHERE year = ? AND month = ? AND zodiac_sign = ?
    """, (year, month, sign_cap))
    dates_row = m_cursor.fetchone()
    m_conn.close()

    try:
        auspicious   = json.loads(dates_row["auspicious_dates"] or "[]") if dates_row else []
        inauspicious = json.loads(dates_row["inauspicious_dates"] or "[]") if dates_row else []
    except Exception:
        auspicious, inauspicious = [], []

    row = dict(row)
    article_text = row["article_text"]   # ← extract to a variable
    parsed = parse_tamil_article(article_text)  # ← no yellow line now ✅


    return {
        "sign"      : sign_cap,
        "tamil_sign": tamil_sign,
        "type"      : "tamil_article",
        "month"     : today.strftime("%B %Y"),
        "title"     : parsed["title"],
        "sections"  : parsed["sections"],
        "auspicious_dates"  : auspicious,
        "inauspicious_dates"  : inauspicious
    }