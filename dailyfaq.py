import os
import json
import re
import sqlite3
from datetime import date, timedelta
from openai import OpenAI
from dotenv import load_dotenv
# ======================================================
# CONFIG
# ======================================================

load_dotenv()

api_key = os.getenv("API_KEY")

if not api_key:
    raise ValueError("API key not found. Check .env file")

client = OpenAI(api_key=api_key)

TODAY = date.today().isoformat()
YESTERDAY = (date.today() - timedelta(days=1)).isoformat()

DB_FILE = "horoscope_faq.db"
HOROSCOPE_FILE = f"horoscope_{TODAY}.jsonl"


# ======================================================
# DATABASE SETUP
# ======================================================

def init_db():
    """Create tables if they don't exist."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_faq (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            date        TEXT NOT NULL,
            moon_sign   TEXT NOT NULL,
            question    TEXT NOT NULL,
            answer      TEXT NOT NULL,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_date_sign
        ON daily_faq (date, moon_sign)
    """)

    conn.commit()
    conn.close()


def save_faq_to_db(sign, faq_list):
    """Insert a list of FAQ dicts for a given sign and date."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    rows = [
        (TODAY, sign, faq["question"], faq["answer"])
        for faq in faq_list
    ]

    cursor.executemany("""
        INSERT INTO daily_faq (date, moon_sign, question, answer)
        VALUES (?, ?, ?, ?)
    """, rows)

    conn.commit()
    conn.close()


def faq_exists_in_db(sign, query_date=TODAY):
    """Check if FAQs already exist for a sign on a given date."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*) FROM daily_faq
        WHERE date = ? AND moon_sign = ?
    """, (query_date, sign))

    count = cursor.fetchone()[0]
    conn.close()

    return count > 0


def load_yesterday_poojas_from_db(sign):
    """Fetch pooja mentions from yesterday's answers to avoid repeats."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT answer FROM daily_faq
        WHERE date = ? AND moon_sign = ?
    """, (YESTERDAY, sign))

    rows = cursor.fetchall()
    conn.close()

    poojas = []
    for (answer,) in rows:
        poojas.extend(re.findall(r"Pooja|Vrata|Japa|Homam|Abhishekam.*", answer))

    return poojas


# ======================================================
# FAQ QUESTIONS
# ======================================================

faq_questions = {
    sign: [
        f"What themes are influencing {sign} today?",
        f"Which areas of life are highlighted right now for {sign}?",
        f"What professional energy surrounds {sign} today?",
        f"What financial patterns are active for {sign}?",
        f"How can {sign} improve communication with others?",
        f"What should {sign} prioritize for physical well-being?",
        f"Which natural strengths are being activated now for {sign}?",
        f"What is unfolding for {sign} over the coming week?",
    ]
    for sign in [
        "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
        "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
    ]
}


# ======================================================
# LOAD TODAY'S HOROSCOPE THEMES (if exists)
# ======================================================

def load_today_horoscope(sign):
    if not os.path.exists(HOROSCOPE_FILE):
        return ""

    try:
        with open(HOROSCOPE_FILE, encoding="utf-8") as f:
            for line in f:
                rec = json.loads(line)
                if rec["moon_sign"] == sign:
                    sections = rec["sections"]
                    return " ".join(sections.values())
    except Exception:
        pass

    return ""


# ======================================================
# AI ANSWER GENERATOR
# ======================================================

def generate_answer(sign, question):
    horoscope_context = load_today_horoscope(sign)
    yesterday_poojas = load_yesterday_poojas_from_db(sign)

    avoid_text = ""
    if yesterday_poojas:
        avoid_text = f"""
Avoid repeating these remedies:
{', '.join(yesterday_poojas[:6])}
"""

    prompt = f"""
You are a Vedic astrologer for AstroVed.com.

DATE: {TODAY}

Moon Sign: {sign}

Today's Horoscope Themes:
{horoscope_context}

Answer this FAQ:

{question}

Include remedies or poojas that MATCH today's horoscope themes.

{avoid_text}

Rules:
- Poojas must change daily
- Must feel specific to today's planetary energy
- Simple at-home rituals only
- Mention at most ONE pooja
- No generic repetition

Tone: spiritual and practical.
Length: 70–100 words.
"""

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.9,
        max_tokens=500,
    )

    return resp.choices[0].message.content.strip()


# ======================================================
# GENERATE DAILY FAQ
# ======================================================

def generate_daily_faq():
    init_db()
    print(f"\n📂 Database: '{DB_FILE}' initialized.")
    print(f"📅 Generating FAQs for: {TODAY}\n")
    print("=" * 60)

    for sign, questions in faq_questions.items():

        if faq_exists_in_db(sign):
            print(f"⚠️  [{sign}] FAQs already exist for today. Skipping.")
            continue

        print(f"\n🔮 Moon Sign: {sign}")
        print("-" * 40)

        faq_list = []

        for i, q in enumerate(questions, 1):
            ans = generate_answer(sign, q)
            faq_list.append({"question": q, "answer": ans})

            print(f"  Q{i}: {q}")
            print(f"  A{i}: {ans}")
            print()

        save_faq_to_db(sign, faq_list)
        print(f"✅ [{sign}] {len(faq_list)} FAQs saved to DB.")
        print("=" * 60)

    print("\n🎉 Daily FAQ generation complete.")


# ======================================================
# RUN
# ======================================================

if __name__ == "__main__":
    generate_daily_faq()