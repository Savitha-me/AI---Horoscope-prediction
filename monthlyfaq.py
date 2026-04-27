import os
import re
import sqlite3
from datetime import date
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

TODAY           = date.today()
CURRENT_MONTH   = TODAY.strftime("%Y-%m")          # e.g. "2026-02"
PREV_MONTH      = TODAY.replace(day=1) 
FAQ_DB_FILE         = "monthly_faq.db"
HOROSCOPE_DB_FILE   = "monthly_horoscope.db"   # ← your existing monthly horoscope DB


def _prev_month():
    """Return the previous month as YYYY-MM string."""
    first = TODAY.replace(day=1)
    last_month = date(first.year - (1 if first.month == 1 else 0),
                      12 if first.month == 1 else first.month - 1, 1)
    return last_month.strftime("%Y-%m")


CURRENT_MONTH   = TODAY.strftime("%Y-%m")
PREV_MONTH      = _prev_month()


# ======================================================
# FAQ QUESTIONS  (monthly flavour)
# ======================================================

faq_questions = {
    sign: [
        f"What are the major themes for {sign} this month?",
        f"Which life areas will see the most growth for {sign} this month?",
        f"What does this month hold professionally for {sign}?",
        f"What financial opportunities or cautions exist for {sign} this month?",
        f"How should {sign} approach relationships and communication this month?",
        f"What health and wellness focus is recommended for {sign} this month?",
        f"Which natural strengths will {sign} rely on most this month?",
        f"What key planetary transits shape {sign}'s month ahead?",
        f"What rituals or remedies will support {sign} through this month?",
        f"How can {sign} best prepare for challenges coming this month?",
    ]
    for sign in [
        "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
        "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
    ]
}


# ======================================================
# MONTHLY HOROSCOPE DB  — read context
# ======================================================

def load_monthly_horoscope(sign, month=CURRENT_MONTH):
    """
    Fetch this month's horoscope text for a sign from the monthly_horoscope DB.

    Expected table schema (adjust column names below if yours differ):
        monthly_horoscope (
            moon_sign   TEXT,
            month       TEXT,   -- format: YYYY-MM
            sections    TEXT    -- JSON string  {"overview": "...", "career": "...", ...}
                                -- OR plain TEXT column
        )
    """
    if not os.path.exists(HOROSCOPE_DB_FILE):
        return ""

    try:
        conn = sqlite3.connect(HOROSCOPE_DB_FILE)
        cursor = conn.cursor()

        # ── Try JSON `sections` column first ──────────────────────────
        try:
            cursor.execute("""
                SELECT sections FROM monthly_horoscope
                WHERE moon_sign = ? AND month = ?
                LIMIT 1
            """, (sign, month))
            row = cursor.fetchone()
            conn.close()

            if row:
                try:
                    import json
                    sections = json.loads(row[0])
                    return " ".join(str(v) for v in sections.values())
                except Exception:
                    return row[0]           # plain text fallback

        except sqlite3.OperationalError:
            # `sections` column doesn't exist — try generic text columns
            pass

        # ── Fallback: concatenate all TEXT columns except keys ─────────
        cursor.execute("""
            SELECT * FROM monthly_horoscope
            WHERE moon_sign = ? AND month = ?
            LIMIT 1
        """, (sign, month))
        row = cursor.fetchone()
        desc = [d[0] for d in cursor.description]
        conn.close()

        if row:
            skip = {"moon_sign", "month", "id", "created_at"}
            parts = [str(v) for k, v in zip(desc, row) if k not in skip and v]
            return " ".join(parts)

    except Exception as e:
        print(f"  ⚠️  Could not read horoscope DB for {sign}: {e}")

    return ""


# ======================================================
# MONTHLY FAQ DB  — write / read
# ======================================================

def init_faq_db():
    conn = sqlite3.connect(FAQ_DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS monthly_faq (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            month       TEXT NOT NULL,
            moon_sign   TEXT NOT NULL,
            question    TEXT NOT NULL,
            answer      TEXT NOT NULL,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_month_sign
        ON monthly_faq (month, moon_sign)
    """)

    conn.commit()
    conn.close()


def faq_exists(sign, month=CURRENT_MONTH):
    conn = sqlite3.connect(FAQ_DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) FROM monthly_faq
        WHERE month = ? AND moon_sign = ?
    """, (month, sign))
    count = cursor.fetchone()[0]
    conn.close()
    return count > 0


def save_faq(sign, faq_list, month=CURRENT_MONTH):
    conn = sqlite3.connect(FAQ_DB_FILE)
    cursor = conn.cursor()
    rows = [(month, sign, f["question"], f["answer"]) for f in faq_list]
    cursor.executemany("""
        INSERT INTO monthly_faq (month, moon_sign, question, answer)
        VALUES (?, ?, ?, ?)
    """, rows)
    conn.commit()
    conn.close()


def load_prev_month_remedies(sign):
    """Avoid repeating last month's poojas/remedies."""
    conn = sqlite3.connect(FAQ_DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT answer FROM monthly_faq
        WHERE month = ? AND moon_sign = ?
    """, (PREV_MONTH, sign))
    rows = cursor.fetchall()
    conn.close()

    remedies = []
    for (answer,) in rows:
        remedies.extend(
            re.findall(r"Pooja|Vrata|Japa|Homam|Abhishekam[^\n.]*", answer)
        )
    return remedies


# ======================================================
# AI ANSWER GENERATOR
# ======================================================

def generate_answer(sign, question, horoscope_context, avoid_remedies):
    avoid_text = ""
    if avoid_remedies:
        avoid_text = f"\nAvoid repeating these remedies from last month:\n{', '.join(avoid_remedies[:6])}\n"

    prompt = f"""
You are a Vedic astrologer for AstroVed.com.

MONTH: {CURRENT_MONTH}
Moon Sign: {sign}

This Month's Horoscope Context:
{horoscope_context if horoscope_context else "No specific horoscope data available — use general Vedic wisdom for this sign and month."}

Answer this monthly FAQ:
{question}

Guidelines:
- Ground your answer in the monthly horoscope themes above.
- If recommending a pooja or remedy, it must feel specific to this month's planetary energy.
- Simple at-home rituals only; mention at most ONE pooja or remedy.
- Poojas must differ from last month's recommendations.
- No generic filler — every sentence should be meaningful.
{avoid_text}
Tone: spiritual, warm, and practical.
Length: 80–110 words.
"""

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.85,
        max_tokens=550,
    )

    return resp.choices[0].message.content.strip()


# ======================================================
# MAIN GENERATOR
# ======================================================

def generate_monthly_faq():
    init_faq_db()

    print(f"\n📂 FAQ Database  : '{FAQ_DB_FILE}' initialized.")
    print(f"📖 Horoscope DB  : '{HOROSCOPE_DB_FILE}'")
    print(f"📅 Generating FAQs for month: {CURRENT_MONTH}\n")
    print("=" * 65)

    for sign, questions in faq_questions.items():

        if faq_exists(sign):
            print(f"⚠️  [{sign}] Monthly FAQs already exist for {CURRENT_MONTH}. Skipping.")
            continue

        # Load context once per sign
        horoscope_context = load_monthly_horoscope(sign)
        avoid_remedies    = load_prev_month_remedies(sign)

        if horoscope_context:
            print(f"\n🔮 Moon Sign: {sign}  ✅ horoscope context loaded ({len(horoscope_context)} chars)")
        else:
            print(f"\n🔮 Moon Sign: {sign}  ⚠️  no horoscope context found — using general Vedic wisdom")

        print("-" * 50)

        faq_list = []

        for i, q in enumerate(questions, 1):
            ans = generate_answer(sign, q, horoscope_context, avoid_remedies)
            faq_list.append({"question": q, "answer": ans})

            print(f"  Q{i}: {q}")
            print(f"  A{i}: {ans}")
            print()

        save_faq(sign, faq_list)
        print(f"✅ [{sign}] {len(faq_list)} FAQs saved to '{FAQ_DB_FILE}'.")
        print("=" * 65)

    print(f"\n🎉 Monthly FAQ generation complete for {CURRENT_MONTH}.")


# ======================================================
# RUN
# ======================================================

if __name__ == "__main__":
    generate_monthly_faq()