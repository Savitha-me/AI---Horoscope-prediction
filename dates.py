import os
import json
import sqlite3
import calendar
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
MONTHLY_DB = "monthly_horoscope.db"

today      = date.today()
year       = today.year
month      = today.month
month_name = today.strftime("%B")
days_in_month = calendar.monthrange(year, month)[1]  # e.g. 28/29/30/31

ZODIACS = [
    "Aries","Taurus","Gemini","Cancer","Leo","Virgo",
    "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"
]


# ======================================================
# FETCH PREDICTIONS FROM DB
# ======================================================

def get_monthly_predictions(sign):
    """Fetch all prediction sections for a sign from the monthly DB."""
    conn   = sqlite3.connect(MONTHLY_DB)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT general, love, finance, career, business, health, student
        FROM monthly_horoscope
        WHERE year=? AND month=? AND zodiac_sign=?
    """, (year, month, sign))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "general" : row[0],
        "love"    : row[1],
        "finance" : row[2],
        "career"  : row[3],
        "business": row[4],
        "health"  : row[5],
        "student" : row[6],
    }


# ======================================================
# AI DATE GENERATOR
# ======================================================

def generate_dates_for_sign(sign, predictions):
    """
    Ask AI to analyze this sign's monthly predictions and return
    unique auspicious and inauspicious dates for the month.
    """

    predictions_text = "\n".join(
        f"{k.capitalize()}: {v}" for k, v in predictions.items()
    )

    prompt = f"""
You are a Vedic astrologer. Based on the monthly horoscope predictions below for {sign},
assign auspicious and inauspicious dates for {month_name} {year}.

The month has {days_in_month} days (1 to {days_in_month}).

Predictions for {sign}:
{predictions_text}

Instructions:
- Analyze the tone, planetary energy, and themes in each section (career, love, finance, health etc.)
- Assign 8 to 10 AUSPICIOUS dates: days when planetary energy is favorable for this sign based on predictions.
- Assign 5 to 6 INAUSPICIOUS dates: days when caution is needed based on challenges mentioned in predictions.
- No date should appear in BOTH lists.
- Dates must be unique and specific to THIS sign's predictions — different signs must have different dates.
- Spread dates throughout the month (beginning, middle, and end).
- Do NOT pick the same pattern for every sign.

Return ONLY valid JSON in this exact format, no explanation:
{{
  "auspicious_dates": [1, 5, 9, 13, 17, 21, 25, 28],
  "inauspicious_dates": [3, 7, 15, 20, 27]
}}
"""

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=200,
    )

    raw = resp.choices[0].message.content.strip()

    # Strip markdown code fences if present
    raw = raw.replace("```json", "").replace("```", "").strip()

    data = json.loads(raw)

    auspicious   = sorted(set(int(d) for d in data["auspicious_dates"]   if 1 <= int(d) <= days_in_month))
    inauspicious = sorted(set(int(d) for d in data["inauspicious_dates"] if 1 <= int(d) <= days_in_month))

    # Ensure no overlap
    inauspicious = [d for d in inauspicious if d not in auspicious]

    return auspicious, inauspicious


# ======================================================
# UPDATE DB
# ======================================================

def update_dates_in_db(sign, auspicious, inauspicious):
    """Write the new dates back into the monthly_horoscope DB."""
    conn   = sqlite3.connect(MONTHLY_DB)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE monthly_horoscope
        SET auspicious_dates   = ?,
            inauspicious_dates = ?
        WHERE year=? AND month=? AND zodiac_sign=?
    """, (
        json.dumps(auspicious),
        json.dumps(inauspicious),
        year, month, sign
    ))
    conn.commit()
    conn.close()


# ======================================================
# MAIN
# ======================================================

def regenerate_all_dates():
    print(f"\n📅 Regenerating auspicious/inauspicious dates for {month_name} {year}")
    print(f"   Month has {days_in_month} days.")
    print("=" * 65)

    for sign in ZODIACS:
        print(f"\n🔮 Processing: {sign}")

        predictions = get_monthly_predictions(sign)

        if not predictions:
            print(f"  ⚠️  No monthly predictions found for {sign}. Skipping.")
            continue

        try:
            auspicious, inauspicious = generate_dates_for_sign(sign, predictions)
            update_dates_in_db(sign, auspicious, inauspicious)

            print(f"  ✅ Auspicious   ({len(auspicious)} dates) : {auspicious}")
            print(f"  ⚠️  Inauspicious ({len(inauspicious)} dates): {inauspicious}")

        except json.JSONDecodeError as e:
            print(f"  ❌ JSON parse error for {sign}: {e}")
        except Exception as e:
            print(f"  ❌ Error for {sign}: {e}")

    print("\n" + "=" * 65)
    print("🎉 Done! All dates updated in monthly_horoscope.db")


if __name__ == "__main__":
    regenerate_all_dates()