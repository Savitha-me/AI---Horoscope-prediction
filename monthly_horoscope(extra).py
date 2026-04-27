import sqlite3
import json
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

# Sections and their writing focus
SECTIONS = {
    "general"  : "overall life themes, personal growth, mindset, and key opportunities this month",
    "love"     : "romantic relationships, emotional connections, compatibility, and relationship advice",
    "finance"  : "money matters, investments, savings, financial decisions, and wealth building",
    "career"   : "professional growth, workplace dynamics, job opportunities, and career strategy",
    "business" : "entrepreneurship, business decisions, partnerships, expansions, and risks",
    "health"   : "physical wellness, mental health, energy levels, lifestyle habits, and self-care",
    "student"  : "academic focus, learning ability, exams, concentration, and educational growth",
}

# ======================================================
# DB SETUP
# ======================================================
conn   = sqlite3.connect("monthly_horoscope.db")
cursor = conn.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS monthly_horoscope (
        year               INTEGER,
        month              INTEGER,
        zodiac_sign        TEXT,
        general            TEXT,
        love               TEXT,
        finance            TEXT,
        career             TEXT,
        business           TEXT,
        health             TEXT,
        student            TEXT,
        auspicious_dates   TEXT,
        inauspicious_dates TEXT,
        PRIMARY KEY (year, month, zodiac_sign)
    )
""")

cursor.execute(
    "SELECT COUNT(*) FROM monthly_horoscope WHERE year=? AND month=?",
    (year, month)
)
if cursor.fetchone()[0] == 12:
    print("Monthly horoscope already generated.")
    conn.close()
    exit()


# ======================================================
# GENERATE ONE SECTION  (~1200-1500 words)
# ======================================================
def generate_section(sign, section_name, section_focus):
    prompt = f"""
You are an expert Vedic astrologer writing a detailed monthly horoscope article for AstroVed.com.

Month     : {month}-{year}
Zodiac    : {sign}
Section   : {section_name.upper()}
Focus     : {section_focus}

Planetary Transits this month:
{TRANSIT_INFO}

Write a detailed, engaging, and astrologically grounded article section for {sign} covering {section_focus}.

Requirements:
- Length: 1200 to 1500 words MINIMUM. This is mandatory.
- Write in flowing paragraphs (no bullet points, no headers inside).
- Include at least 8 to 10 full paragraphs.
- Each paragraph must be 4 to 6 sentences minimum.
- Ground every insight in the planetary transits listed above.
- Be specific to {sign}'s traits, ruling planet, and elemental nature.
- Tone: warm, spiritual, practical, and predictive.
- Do NOT use generic filler. Every paragraph must add new insight.
- Do NOT start with "{sign}" or "This month". Vary your opening.

Return ONLY the plain article text. No JSON. No headers. No labels.
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.85,
        max_tokens=2200,   # enough headroom for 1500 words
    )

    return response.choices[0].message.content.strip()


# ======================================================
# GENERATE UNIQUE DATES PER SIGN
# ======================================================
def generate_dates(sign, sections_summary):
    prompt = f"""
You are a Vedic astrologer assigning auspicious and inauspicious dates for {sign} in month {month}-{year}.

Here is a summary of {sign}'s monthly predictions:
{sections_summary}

Planetary Transits:
{TRANSIT_INFO}

Based on the planetary energy and the specific themes in {sign}'s predictions:
- Assign 4 to 6 AUSPICIOUS dates (favorable days based on planetary support).
- Assign 3 to 5 INAUSPICIOUS dates (challenging days needing caution).
- Dates must be between 1 and 31.
- No date should appear in both lists.
- Dates must be UNIQUE to {sign} — do not use the same dates as other signs.
- Spread them across the beginning, middle, and end of the month.

Return ONLY valid JSON:
{{
  "auspicious_dates": [],
  "inauspicious_dates": []
}}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=200,
    )

    text = response.choices[0].message.content.strip()
    text = text.replace("```json", "").replace("```", "").strip()
    data = json.loads(text)

    auspicious   = sorted(set(int(d) for d in data["auspicious_dates"]   if 1 <= int(d) <= 31))
    inauspicious = sorted(set(int(d) for d in data["inauspicious_dates"] if 1 <= int(d) <= 31))
    inauspicious = [d for d in inauspicious if d not in auspicious]

    return auspicious, inauspicious


# ======================================================
# MAIN LOOP
# ======================================================
for sign in ZODIACS:
    print(f"\n🔮 Generating: {sign}")
    print("-" * 50)

    section_data = {}

    # Generate each section separately for full word count
    for section_name, section_focus in SECTIONS.items():
        print(f"  ✍️  Writing {section_name} section...")
        text = generate_section(sign, section_name, section_focus)
        section_data[section_name] = text
        word_count = len(text.split())
        print(f"  ✅ {section_name}: {word_count} words")

    # Generate unique dates using the general + career summary as context
    print(f"  📅 Generating unique dates for {sign}...")
    summary = section_data["general"][:500] + " " + section_data["career"][:300]
    auspicious, inauspicious = generate_dates(sign, summary)
    print(f"  🌟 Auspicious   : {auspicious}")
    print(f"  ⚠️  Inauspicious : {inauspicious}")

    # Save to DB
    cursor.execute("""
        INSERT OR REPLACE INTO monthly_horoscope
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        year,
        month,
        sign,
        section_data["general"],
        section_data["love"],
        section_data["finance"],
        section_data["career"],
        section_data["business"],
        section_data["health"],
        section_data["student"],
        json.dumps(auspicious),
        json.dumps(inauspicious),
    ))
    conn.commit()
    print(f"  💾 {sign} saved to DB.")

conn.close()
print("\n✅ All 12 signs generated successfully.")