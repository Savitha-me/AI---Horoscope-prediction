import sqlite3
import hashlib
from datetime import date
from openai import OpenAI
from dotenv import load_dotenv
import os

# ======================================================
# CONFIG
# ======================================================
load_dotenv()
api_key = os.getenv("API_KEY")

if not api_key:
    raise ValueError("API key not found")

client = OpenAI(api_key=api_key)

DB_FILE = "monthly_article.db"
TABLE   = "monthly_articles"

ZODIACS = [
    "Aries","Taurus","Gemini","Cancer","Leo","Virgo",
    "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"
]

today      = date.today()
year       = today.year
month      = today.month
month_name = today.strftime("%B")

# ======================================================
# COMMON MONTHLY POOJA (Used by Tamil also)
# ======================================================
POOJAS = [
    "Navagraha Pooja",
    "Mahalakshmi Pooja",
    "Ganesha Pooja",
    "Shani Pooja",
    "Mars Pooja",
    "Chandra Pooja",
    "Surya Pooja",
    "Shukra Pooja",
    "Guru Pooja",
    "Durga Pooja"
]

def get_monthly_pooja(sign, section):
    key = f"{sign}_{section}_{year}_{month}"
    h = hashlib.md5(key.encode()).hexdigest()
    index = int(h[:6], 16) % len(POOJAS)
    return POOJAS[index]

# ======================================================
# DATABASE
# ======================================================
conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

cursor.execute(f"""
CREATE TABLE IF NOT EXISTS {TABLE} (
    year INTEGER,
    month INTEGER,
    zodiac_sign TEXT,
    article_text TEXT,
    PRIMARY KEY (year, month, zodiac_sign)
)
""")
conn.commit()

# ======================================================
# WORD COUNT
# ======================================================
def count_words(text):
    return len(text.split())

# ======================================================
# GENERATE ENGLISH ARTICLE
# ======================================================
def generate_article(sign):

    prompt = f"""
Write a detailed Vedic astrology monthly article.

Month: {month_name} {year}
Zodiac: {sign}

Requirements:
- 900–1100 words
- Professional astrology tone
- Second person (you/your)
- Plain text only
- No remedies or poojas

Structure EXACTLY:

Heading 1: {sign} Monthly Horoscope - {month_name} {year}

Heading 2: Overview

Heading 2: Love & Relationships

Heading 2: Finance & Wealth

Heading 2: Career & Professional Growth

Heading 2: Business

Heading 2: Health & Wellness

Heading 2: Education & Learning
"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8,
        max_tokens=3200
    )

    article = response.choices[0].message.content.strip()

    # Ensure length
    if count_words(article) < 850:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{
                "role": "user",
                "content": f"Expand this to 900+ words without changing headings:\n\n{article}"
            }],
            temperature=0.7,
            max_tokens=2000
        )
        article = response.choices[0].message.content.strip()

    return article

# ======================================================
# INJECT POOJA
# ======================================================
def inject_poojas(sign, text):

    lines = text.split("\n")
    output = []
    current_section = None

    for line in lines:
        s = line.strip()

        if s.startswith("Heading 2:"):
            if current_section:
                pooja = get_monthly_pooja(sign, current_section)
                output.append(f"Divine technique: {pooja}\n")

            current_section = s.replace("Heading 2:", "").strip()
            output.append(line)
        else:
            output.append(line)

    if current_section:
        pooja = get_monthly_pooja(sign, current_section)
        output.append(f"Divine technique: {pooja}")

    return "\n".join(output)

# ======================================================
# MAIN
# ======================================================
print(f"Generating English Articles for {month_name} {year}")

for sign in ZODIACS:

    cursor.execute(f"""
    SELECT article_text FROM {TABLE}
    WHERE year=? AND month=? AND zodiac_sign=?
    """, (year, month, sign))

    if cursor.fetchone():
        print(sign, "exists")
        continue

    raw = generate_article(sign)
    final = inject_poojas(sign, raw)

    cursor.execute(f"""
    INSERT INTO {TABLE}
    VALUES (?, ?, ?, ?)
    """, (year, month, sign, final))

    conn.commit()
    print(sign, "saved")

conn.close()