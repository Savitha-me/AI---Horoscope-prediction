import sqlite3
import json
import re
from datetime import date
from openai import OpenAI
from dotenv import load_dotenv
import hashlib
import os

# ===============================
# Load API Key
# ===============================
load_dotenv()

api_key = os.getenv("API_KEY")
if not api_key:
    raise ValueError("API key not found. Check .env file")

client = OpenAI(api_key=api_key)

# ===============================
# Config
# ===============================
ZODIACS = [
    "Aries","Taurus","Gemini","Cancer","Leo","Virgo",
    "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"
]

COLORS = [
    "Red","Blue","Green","Yellow","White",
    "Pink","Orange","Purple","Brown","Grey","Gold","Silver"
]

POOJA_FILE = "temple_links.json"

# ===============================
# Load Pooja List
# ===============================
def load_poojas():
    with open(POOJA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

POOJAS      = load_poojas()
POOJA_MAP   = {p["name"]: p["link"] for p in POOJAS}
POOJA_NAMES = list(POOJA_MAP.keys())

# ===============================
# Lucky Color / Number (deterministic)
# ===============================
def get_daily_lucky(sign, date_str):
    h            = hashlib.md5((sign + date_str).encode()).hexdigest()
    color_index  = int(h[:2], 16) % len(COLORS)
    lucky_number = (int(h[2:6], 16) % 9) + 1
    return COLORS[color_index], lucky_number

# ===============================
# JSON Cleaner
# ===============================
def clean_json(text):
    text = text.replace("```json", "").replace("```", "").strip()
    text = re.sub(r",\s*([\}\]])", r"\1", text)
    return text

# ===============================
# Database Setup
# ===============================
DB_FILE = "daily_horoscope_prediction.db"
TABLE   = "daily_horoscope"

conn   = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

cursor.execute(f"""
    CREATE TABLE IF NOT EXISTS {TABLE} (
        date           TEXT,
        zodiac_sign    TEXT,
        general        TEXT,
        career         TEXT,
        love           TEXT,
        finance        TEXT,
        health         TEXT,
        lucky_color    TEXT,
        lucky_number   INTEGER,
        pooja_1_name   TEXT,
        pooja_1_link   TEXT,
        pooja_1_reason TEXT,
        pooja_2_name   TEXT,
        pooja_2_link   TEXT,
        pooja_2_reason TEXT,
        PRIMARY KEY (date, zodiac_sign)
    )
""")

today = str(date.today())

cursor.execute(f"SELECT COUNT(*) FROM {TABLE} WHERE date=?", (today,))
if cursor.fetchone()[0] == 12:
    print("Today's horoscope already generated.")
    conn.close()
    exit()

# ===============================
# Generate Daily Prediction
# ===============================
def generate_daily(sign, attempt=1):
    prompt = f"""
You are a Vedic astrologer. Generate a DAILY horoscope for {sign} for {today}.

Requirements:
- Each section: 3 to 4 meaningful sentences.
- Tone: practical, warm, and astrologically grounded.
- Be specific to {sign}'s traits and ruling planet.
- IMPORTANT: Return ONLY strictly valid JSON. No trailing commas. No extra text.

Return ONLY valid JSON:
{{
    "general"  : "",
    "career"   : "",
    "love"     : "",
    "finance"  : "",
    "health"   : ""
}}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=800,
    )

    text = clean_json(response.choices[0].message.content.strip())

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        if attempt < 3:
            print(f"  JSON error attempt {attempt} for {sign}: {e}. Retrying...")
            return generate_daily(sign, attempt + 1)
        text = text[text.find("{"):text.rfind("}")+1]
        return json.loads(text)


# ===============================
# Recommend TWO Poojas with Reasons
# ===============================
def recommend_poojas(sign, prediction, attempt=1):
    prompt = f"""
You are a Vedic astrologer. Based on the daily horoscope prediction below for {sign},
recommend exactly TWO poojas from the list provided, with a specific reason for each.

Today's prediction for {sign}:
General  : {prediction['general']}
Career   : {prediction['career']}
Love     : {prediction['love']}
Finance  : {prediction['finance']}
Health   : {prediction['health']}

Available Poojas (choose EXACTLY two different names from this list):
{json.dumps(POOJA_NAMES, indent=2)}

Rules:
- Pick TWO poojas that best match today's planetary energy and prediction themes.
- Both poojas must be DIFFERENT from each other.
- For each pooja write a reason of 2 to 3 sentences explaining WHY this specific pooja
  is recommended for {sign} today, based on the prediction content above.
- Recommendations and reasons must CHANGE daily based on the prediction content.
- IMPORTANT: Return ONLY strictly valid JSON. No trailing commas. No extra text.

Return ONLY valid JSON:
{{
    "pooja_1": {{
        "name"  : "<exact name from list>",
        "reason": "<2-3 sentences why this pooja suits today's energy for {sign}>"
    }},
    "pooja_2": {{
        "name"  : "<exact name from list>",
        "reason": "<2-3 sentences why this pooja suits today's energy for {sign}>"
    }}
}}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.6,
        max_tokens=400,
    )

    text = clean_json(response.choices[0].message.content.strip())

    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        if attempt < 3:
            print(f"  Pooja JSON error attempt {attempt} for {sign}: {e}. Retrying...")
            return recommend_poojas(sign, prediction, attempt + 1)
        return [
            ("Navagraha Pooja", POOJA_MAP["Navagraha Pooja"],
             "Navagraha Pooja harmonizes all planetary influences affecting you today."),
            ("Lakshmi Pooja",   POOJA_MAP["Lakshmi Pooja"],
             "Lakshmi Pooja invites abundance and positive energy into your day."),
        ]

    def resolve(entry):
        name   = entry.get("name", "")
        reason = entry.get("reason", "")
        if name in POOJA_MAP:
            return name, POOJA_MAP[name], reason
        for pname in POOJA_NAMES:
            if name.lower() in pname.lower() or pname.lower() in name.lower():
                return pname, POOJA_MAP[pname], reason
        return "Navagraha Pooja", POOJA_MAP["Navagraha Pooja"], reason

    p1 = resolve(data.get("pooja_1", {}))
    p2 = resolve(data.get("pooja_2", {}))

    if p1[0] == p2[0]:
        p2 = ("Lakshmi Pooja", POOJA_MAP["Lakshmi Pooja"],
              "Lakshmi Pooja brings additional grace and prosperity to complement today's energy.")

    return [p1, p2]


# ===============================
# Main Loop
# ===============================
print(f"\nGenerating daily horoscope for {today}")
print("=" * 55)

for sign in ZODIACS:
    print(f"\n  {sign}")
    print("  " + "-" * 35)

    print("  Generating prediction...")
    prediction = generate_daily(sign)

    lucky_color, lucky_number = get_daily_lucky(sign, today)

    print("  Recommending two poojas with reasons...")
    poojas = recommend_poojas(sign, prediction)
    p1_name, p1_link, p1_reason = poojas[0]
    p2_name, p2_link, p2_reason = poojas[1]

    print(f"     Lucky Color : {lucky_color}")
    print(f"     Lucky Number: {lucky_number}")
    print(f"     Pooja 1     : {p1_name}")
    print(f"     Reason 1    : {p1_reason[:80]}...")
    print(f"     Pooja 2     : {p2_name}")
    print(f"     Reason 2    : {p2_reason[:80]}...")

    cursor.execute(f"""
        INSERT OR REPLACE INTO {TABLE}
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        today, sign,
        prediction["general"],
        prediction["career"],
        prediction["love"],
        prediction["finance"],
        prediction["health"],
        lucky_color,
        lucky_number,
        p1_name, p1_link, p1_reason,
        p2_name, p2_link, p2_reason,
    ))

    conn.commit()
    print(f"  {sign} saved.")

conn.close()
print(f"\nDaily horoscope generated for all 12 signs.")