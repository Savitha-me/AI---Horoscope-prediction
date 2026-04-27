import sqlite3
import json
import re
from datetime import date
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv("API_KEY")
if not api_key:
    raise ValueError("API key not found. Check .env file")

client = OpenAI(api_key=api_key)

ZODIACS = [
    "Aries","Taurus","Gemini","Cancer","Leo","Virgo",
    "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"
]

today = date.today()
year  = today.year
month = today.month

TRANSIT_INFO = """
Jupiter in Taurus.
Saturn in Pisces.
Mercury retrograde mid-month.
Moon cycles influence emotions and finances.
"""

# ======================================================
# DIVINE TECHNIQUE MAPPING — ALL 7 SECTIONS
# ======================================================
DIVINE_MAP = {
    "general"  : ("Overall Life",  "Saturn Pooja"),
    "love"     : ("Relationships", "Mars Pooja"),
    "finance"  : ("Finance",       "Venus Pooja"),
    "career"   : ("Career",        "Moon Pooja"),
    "business" : ("Business",      "Mercury Pooja"),
    "health"   : ("Health",        "Sun Pooja"),
    "student"  : ("Education",     "Jupiter Pooja"),
}

def build_divine_line(section_key):
    topic, pooja = DIVINE_MAP[section_key]
    return f"Divine technique to improve your {topic}: {pooja}"

def append_divine(section_key, narrative_text):
    return narrative_text.strip() + "\n" + build_divine_line(section_key)

# ======================================================
# DB SETUP
# ======================================================
DB_FILE = "monthly_horoscope.db"
TABLE   = "monthly_horoscope"

conn   = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

cursor.execute(f"""
    CREATE TABLE IF NOT EXISTS {TABLE} (
        year                INTEGER,
        month               INTEGER,
        zodiac_sign         TEXT,
        general             TEXT,
        love                TEXT,
        finance             TEXT,
        career              TEXT,
        business            TEXT,
        health              TEXT,
        student             TEXT,
        general_article     TEXT,
        love_article        TEXT,
        finance_article     TEXT,
        career_article      TEXT,
        business_article    TEXT,
        health_article      TEXT,
        student_article     TEXT,
        auspicious_dates    TEXT,
        inauspicious_dates  TEXT,
        article_text        TEXT,
        love_pooja          TEXT,
        career_pooja        TEXT,
        finance_pooja       TEXT,
        health_pooja        TEXT,
        education_pooja     TEXT,
        PRIMARY KEY (year, month, zodiac_sign)
    )
""")

# Add any missing columns to existing DB safely
def ensure_columns():
    cursor.execute(f"PRAGMA table_info({TABLE})")
    existing = [col[1] for col in cursor.fetchall()]
    needed = [
        "article_text", "love_pooja", "career_pooja",
        "finance_pooja", "health_pooja", "education_pooja"
    ]
    for col in needed:
        if col not in existing:
            cursor.execute(f"ALTER TABLE {TABLE} ADD COLUMN {col} TEXT")
            print(f"  Added column: {col}")
    conn.commit()

ensure_columns()

cursor.execute(
    f"SELECT COUNT(*) FROM {TABLE} WHERE year=? AND month=? AND general IS NOT NULL",
    (year, month)
)
if cursor.fetchone()[0] == 12:
    print("Short predictions already generated for this month.")
    conn.close()
    exit()

# ======================================================
# JSON CLEANER
# ======================================================
def clean_json(text):
    text = re.sub(r"```json\s*", "", text)
    text = re.sub(r"```\s*", "", text)
    text = text.strip()
    text = re.sub(r",\s*([\}\]])", r"\1", text)
    return text

# ======================================================
# GENERATE PREDICTIONS — pure narrative, no Divine lines
# Divine lines appended by Python to avoid JSON corruption
# ======================================================
def generate_short_predictions(sign, attempt=1):
    prompt = f"""You are a Vedic astrologer writing monthly horoscope predictions for {sign}.

Month: {month}-{year}
Planetary Transits:
{TRANSIT_INFO}

Write ONLY the narrative prediction text for each section.
Do NOT include any "Divine technique" lines.
Do NOT include section headings or labels inside the text.

Word count per section:
- general  : 100 to 120 words
- love     : 110 to 130 words
- finance  : 40  to 60  words
- career   : 110 to 130 words
- business : 50  to 70  words
- health   : 50  to 70  words
- student  : 70  to 90  words

Style: 2-3 paragraphs, practical, future-tense ("may", "could", "might").
Specific to {sign}'s traits. Job-role specificity in General and Career.

CRITICAL JSON RULES:
- Return ONLY a single valid JSON object.
- All values on ONE LINE — no literal newlines inside values.
- Separate paragraphs with token {{PARA}}.
- No trailing commas. No markdown.

Format:
{{
    "general"  : "paragraph1 {{PARA}} paragraph2 {{PARA}} paragraph3",
    "love"     : "paragraph1 {{PARA}} paragraph2",
    "finance"  : "paragraph1 {{PARA}} paragraph2",
    "career"   : "paragraph1 {{PARA}} paragraph2 {{PARA}} paragraph3",
    "business" : "paragraph1 {{PARA}} paragraph2",
    "health"   : "paragraph1 {{PARA}} paragraph2",
    "student"  : "paragraph1 {{PARA}} paragraph2"
}}"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.85,
        max_tokens=2400,
    )

    raw  = response.choices[0].message.content.strip()
    text = clean_json(raw)

    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        if attempt < 4:
            print(f"  JSON error (attempt {attempt}) for {sign}: {e}. Retrying...")
            return generate_short_predictions(sign, attempt + 1)
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            data = json.loads(match.group())
        else:
            raise

    sections = ["general", "love", "finance", "career", "business", "health", "student"]
    result   = {}
    for sec in sections:
        narrative = data.get(sec, "").strip()
        narrative = narrative.replace("{PARA}", "\n").replace("{ PARA }", "\n")
        lines     = [l for l in narrative.split("\n") if not l.strip().lower().startswith("divine technique")]
        narrative = "\n".join(lines).strip()
        result[sec] = append_divine(sec, narrative)

    return result

# ======================================================
# GENERATE DATES
# ======================================================
def generate_dates(sign, general_preview, attempt=1):
    prompt = f"""Vedic astrologer assigning dates for {sign} in {month}-{year}.
Preview: {general_preview}
Transits: {TRANSIT_INFO}

Rules: 4-6 auspicious, 3-5 inauspicious, between 1-31, no overlap, spread across month.

Return ONLY valid JSON:
{{
  "auspicious_dates": [],
  "inauspicious_dates": []
}}"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=200,
    )

    text = clean_json(response.choices[0].message.content.strip())
    try:
        data         = json.loads(text)
        auspicious   = sorted(set(int(d) for d in data["auspicious_dates"]   if 1 <= int(d) <= 31))
        inauspicious = sorted(set(int(d) for d in data["inauspicious_dates"] if 1 <= int(d) <= 31))
        inauspicious = [d for d in inauspicious if d not in auspicious]
        return auspicious, inauspicious
    except Exception as e:
        if attempt < 3:
            return generate_dates(sign, general_preview, attempt + 1)
        return [3, 7, 14, 21, 28], [5, 12, 19]

# ======================================================
# MAIN LOOP
# ======================================================
print(f"\nGenerating monthly predictions for {month}-{year}")
print("=" * 55)

for sign in ZODIACS:
    print(f"\n{sign}")
    print("-" * 40)

    short = generate_short_predictions(sign)

    for sec in ["general", "love", "finance", "career", "business", "health", "student"]:
        wc = len([l for l in short[sec].split("\n") if not l.lower().startswith("divine technique")])
        print(f"     {sec:<10}: saved  →  {build_divine_line(sec)}")

    preview = "\n".join(l for l in short["general"].split("\n")
                        if not l.strip().lower().startswith("divine technique"))[:400]
    auspicious, inauspicious = generate_dates(sign, preview)
    print(f"     Auspicious: {auspicious}  |  Inauspicious: {inauspicious}")

    cursor.execute(f"""
        INSERT OR REPLACE INTO {TABLE}
        (year, month, zodiac_sign,
         general, love, finance, career, business, health, student,
         auspicious_dates, inauspicious_dates)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        year, month, sign,
        short["general"], short["love"], short["finance"], short["career"],
        short["business"], short["health"], short["student"],
        json.dumps(auspicious), json.dumps(inauspicious),
    ))
    conn.commit()
    print(f"  ✓ {sign} saved.")

conn.close()
print("\n✓ All predictions saved. Now run: python monthly_article_generator.py")