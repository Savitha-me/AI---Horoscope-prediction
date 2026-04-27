import sqlite3
import hashlib
from datetime import date
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv("API_KEY")

if not api_key:
    raise ValueError("API key not found")

client = OpenAI(api_key=api_key)

# ======================================================
# CONFIG
# ======================================================
MONTHLY_DB  = "monthly_horoscope.db"   # English source DB
TAMIL_DB    = "monthly_article_tamil.db"
TABLE       = "monthly_articles_tamil"

ZODIACS_ENGLISH = [
    "Aries","Taurus","Gemini","Cancer","Leo","Virgo",
    "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"
]

ZODIACS_TAMIL = [
    "மேஷம்","ரிஷபம்","மிதுனம்","கடகம்","சிம்மம்","கன்னி",
    "துலாம்","விருச்சிகம்","தனுசு","மகரம்","கும்பம்","மீனம்"
]

# English sign → Tamil sign mapping
EN_TO_TAMIL = dict(zip(ZODIACS_ENGLISH, ZODIACS_TAMIL))

today      = date.today()
year       = today.year
month      = today.month
month_name = today.strftime("%B")

# ======================================================
# SECTION MAP
# English DB column  →  (Tamil heading, English heading label)
# ======================================================
SECTIONS = [
    ("general",  "பொதுப்பலன்",                  "Overview"),
    ("love",     "காதல் / குடும்ப உறவு",              "Love & Relationships"),
    ("finance",  "நிதிநிலை ",               "Finance & Wealth"),
    ("career",   "உத்தியோகம்",    "Career & Professional Growth"),
    ("business", "தொழில்",                          "Business"),
    ("health",   "ஆரோக்கியம் ",          "Health & Wellness"),
    ("student",  "மாணவர்கள்",               "Education & Learning"),
]
# ======================================================
# DATABASE SETUP
# ======================================================
tamil_conn   = sqlite3.connect(TAMIL_DB)
tamil_cursor = tamil_conn.cursor()

tamil_cursor.execute(f"""
CREATE TABLE IF NOT EXISTS {TABLE} (
    year        INTEGER,
    month       INTEGER,
    zodiac_sign TEXT,
    article_text TEXT,
    PRIMARY KEY (year, month, zodiac_sign)
)
""")
tamil_conn.commit()

# ======================================================
# FETCH ENGLISH SECTION CONTENT
# ======================================================
def fetch_english_sections(en_sign):
    """
    Returns a dict: {col_name: content_text}
    fetched from monthly_horoscope.db for the given English sign.
    """
    if not os.path.exists(MONTHLY_DB):
        print(f"  ⚠ {MONTHLY_DB} not found — skipping English source")
        return {}

    conn = sqlite3.connect(MONTHLY_DB)
    cur  = conn.cursor()
    try:
        cur.execute("""
            SELECT general, love, finance, career, business, health, student
            FROM monthly_horoscope
            WHERE zodiac_sign=? AND year=? AND month=?
        """, (en_sign, year, month))
        row = cur.fetchone()
        if not row:
            print(f"  ⚠ No English data found for {en_sign} {month}/{year}")
            return {}
        cols = ["general","love","finance","career","business","health","student"]
        return {col: (row[i] or "").strip() for i, col in enumerate(cols)}
    except Exception as e:
        print(f"  ⚠ DB error: {e}")
        return {}
    finally:
        conn.close()

def clean_english_text(text):
    """Remove old embedded pooja/remedy lines from English content."""
    lines = []
    for line in text.split("\n"):
        sl = line.strip().lower()
        if sl.startswith("divine technique") or sl.startswith("remedy:"):
            continue
        lines.append(line)
    return "\n".join(lines).strip()

import re as _re
_FOREIGN_RE = _re.compile(
    r'[\u4e00-\u9fff'   # CJK (Chinese/Japanese/Korean)
    r'\u3040-\u30ff'    # Hiragana/Katakana
    r'\uac00-\ud7af'    # Korean Hangul
    r'\u0600-\u06ff'    # Arabic
    r'\u0900-\u097f]'   # Devanagari
)
_ECHO_PREFIXES = ("ராசி:", "பிரிவு:", "rasi:", "section:", "piriv")

def clean_gpt_output(text):
    """
    Strip from GPT paragraph output:
    - Prompt echo lines (ராசி:, பிரிவு:, etc.)
    - Foreign-script characters (Chinese 方面, etc.)
    """
    lines = []
    for line in text.split("\n"):
        s = line.strip()
        if not s:
            lines.append("")
            continue
        # Drop prompt echo lines
        if any(s.lower().startswith(p) for p in _ECHO_PREFIXES):
            continue
        # Strip foreign chars inline
        s = _FOREIGN_RE.sub("", s).strip()
        if s:
            lines.append(s)
    return "\n".join(lines).strip()

# ======================================================
# GPT HELPERS
# ======================================================
def translate_to_tamil(english_text, section_tamil, sign_tamil):
    """
    Translate the English paragraph to Tamil naturally.
    Returns a single Tamil paragraph (~80-120 words).
    """
    prompt = f"""
நீங்கள் ஒரு வேத ஜோதிட நிபுணர். கீழே உள்ள ஆங்கில ஜோதிட உரையை இயல்பான, தெளிவான தமிழில் மொழிபெயர்க்கவும்.

ராசி: {sign_tamil}
பிரிவு: {section_tamil}

ஆங்கில உரை:
{english_text}

விதிகள்:
- நேரடி மொழிபெயர்ப்பு செய்யவும், அர்த்தம் மாறாமல் இருக்கட்டும்
- இயல்பான தமிழ் நடையில் எழுதவும்
- ஒரே ஒரு பத்தி மட்டும் (80–120 வார்த்தைகள்)
- பூஜை பரிந்துரைகள், தலைப்புகள் சேர்க்கவேண்டாம்
- "ராசி:", "பிரிவு:", "Rasi:", "Section:" போன்ற வரிகளை சேர்க்கவேண்டாம்
- தமிழில் மட்டும் பதிலளிக்கவும் — சீன, ஜப்பானிய, அரபி எழுத்துகள் வேண்டவே வேண்டாம்
- நேரடியாக பத்தியை மட்டும் எழுதவும், வேறு எந்த முன்னுரையும் வேண்டாம்
"""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,
        max_tokens=400
    )
    return response.choices[0].message.content.strip()


def generate_original_tamil(section_tamil, sign_tamil, english_context):
    """
    Generate a fresh, original Tamil paragraph for the section.
    Uses English context to avoid repeating the same points.
    Returns a single Tamil paragraph (~100-130 words).
    """
    prompt = f"""
நீங்கள் ஒரு வேத ஜோதிட நிபுணர். {sign_tamil} ராசிக்கான {month_name} {year} மாத ராசிபலனில் "{section_tamil}" பிரிவுக்கு ஒரு புதிய, தனித்துவமான தமிழ் பத்தி எழுதவும்.

கீழே உள்ள கருத்துகள் ஏற்கனவே சொல்லப்பட்டுவிட்டன — இவற்றை திரும்ப சொல்லாதீர்கள்:
{english_context}

விதிகள்:
- புதிய கோணத்தில் கூடுதல் ஆலோசனைகள், நடைமுறை குறிப்புகள் அல்லது கிரக தாக்கங்களை விவரிக்கவும்
- ஒரே ஒரு பத்தி மட்டும் (சரியாக 43 வார்த்தைகள் — அதிகமாகவோ குறைவாகவோ இருக்கவேண்டாம்)
- பூஜை பரிந்துரைகள், தலைப்புகள் சேர்க்கவேண்டாம்
- "ராசி:", "பிரிவு:", "Rasi:", "Section:" போன்ற வரிகளை சேர்க்கவேண்டாம்
- தமிழில் மட்டும் பதிலளிக்கவும் — சீன, ஜப்பானிய, அரபி எழுத்துகள் வேண்டவே வேண்டாம்
- நேரடியாக பத்தியை மட்டும் எழுதவும், வேறு எந்த முன்னுரையும் வேண்டாம்
"""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.85,
        max_tokens=150
    )
    return response.choices[0].message.content.strip()


# ======================================================
# BUILD FULL ARTICLE
# ======================================================
def build_article(en_sign, ta_sign, english_sections):
    """
    Build the full Tamil article.
    Each H2 section gets:
      Paragraph 1 — translated from English content
      Paragraph 2 — freshly generated original Tamil content
    """
    lines = []

    # H1 title
    lines.append(f"Heading 1: {ta_sign} மாத ராசிபலன் - {month_name} {year}")
    lines.append("")

    for col, ta_heading, en_heading in SECTIONS:
        en_text = english_sections.get(col, "")

        print(f"    [{ta_heading}] translating...", end=" ", flush=True)

        # ── Paragraph 1: Translated from English ──────────
        if en_text:
            cleaned_en = clean_english_text(en_text)
            para1 = clean_gpt_output(translate_to_tamil(cleaned_en, ta_heading, ta_sign))
        else:
            para1 = clean_gpt_output(generate_original_tamil(ta_heading, ta_sign, ""))

        print("generating original...", end=" ", flush=True)

        # ── Paragraph 2: Original Tamil content ───────────
        para2 = clean_gpt_output(generate_original_tamil(ta_heading, ta_sign, en_text))

        print("✓")

        lines.append(f"Heading 2: {ta_heading}")
        lines.append("")
        lines.append(para1)
        lines.append("")
        lines.append(para2)
        lines.append("")

    return "\n".join(lines)


# ======================================================
# MAIN
# ======================================================
print(f"\n{'='*60}")
print(f"Generating Tamil Articles — {month_name} {year}")
print(f"{'='*60}\n")

for en_sign, ta_sign in zip(ZODIACS_ENGLISH, ZODIACS_TAMIL):

    # Check if already exists
    tamil_cursor.execute(f"""
        SELECT article_text FROM {TABLE}
        WHERE year=? AND month=? AND zodiac_sign=?
    """, (year, month, ta_sign))

    if tamil_cursor.fetchone():
        print(f"  ⏭  {ta_sign} ({en_sign}) — already exists, skipping")
        continue

    print(f"\n  🔄  {ta_sign} ({en_sign})")

    # Fetch English source content
    english_sections = fetch_english_sections(en_sign)

    # Build the article
    article_text = build_article(en_sign, ta_sign, english_sections)

    # Save to DB
    tamil_cursor.execute(f"""
        INSERT INTO {TABLE} (year, month, zodiac_sign, article_text)
        VALUES (?, ?, ?, ?)
    """, (year, month, ta_sign, article_text))
    tamil_conn.commit()

    word_count = len(article_text.split())
    print(f"  ✅  {ta_sign} saved — {word_count} words")

tamil_conn.close()
print(f"\n{'='*60}")
print("Done!")
print(f"{'='*60}\n")