import streamlit as st
import sqlite3
import json
import random
from datetime import date

# --------------------------------------------------
# CONFIG
# --------------------------------------------------
DB_PATH = "monthly_horoscope.db"
POOJA_FILE = "temple_links.json"

ZODIACS = [
    "Aries","Taurus","Gemini","Cancer","Leo","Virgo",
    "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"
]

today = date.today()
year = today.year
month = today.month

st.set_page_config(page_title="Monthly Article", layout="wide")
st.title("🔮 Monthly Horoscope Article")

# --------------------------------------------------
# LOAD POOJA LINKS
# --------------------------------------------------
@st.cache_data
def load_poojas():
    with open(POOJA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

POOJAS = load_poojas()

def get_random_pooja():
    pooja = random.choice(POOJAS)
    return pooja["name"], pooja["link"]


# --------------------------------------------------
# DATABASE FUNCTION
# --------------------------------------------------
def get_monthly_data(sign):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    SELECT general, love, finance, career, business, health, student,
           auspicious_dates, inauspicious_dates
    FROM monthly_horoscope
    WHERE year=? AND month=? AND zodiac_sign=?
    """, (year, month, sign))

    data = cursor.fetchone()
    conn.close()

    if not data:
        return None

    return {
        "general": data[0],
        "love": data[1],
        "finance": data[2],
        "career": data[3],
        "business": data[4],
        "health": data[5],
        "student": data[6],
        "auspicious": json.loads(data[7]),
        "inauspicious": json.loads(data[8])
    }


# --------------------------------------------------
# UI
# --------------------------------------------------
selected_sign = st.selectbox("Select Zodiac Sign", ZODIACS)

data = get_monthly_data(selected_sign)

if data:

    st.header(f"{selected_sign} Horoscope - {month}/{year}")

    sections = [
        ("General", data["general"]),
        ("Relationships", data["love"]),
        ("Finances", data["finance"]),
        ("Career", data["career"]),
        ("Business", data["business"]),
        ("Health", data["health"]),
        ("Education", data["student"])
    ]

    for title, content in sections:
        pooja_name, pooja_link = get_random_pooja()

        st.subheader(title)
        st.write(content)

        # AstroVed-style line
        st.markdown(
            f"**Divine technique to improve your {title}: "
            f"[{pooja_name}]({pooja_link})**"
        )

    # Dates
    st.subheader("Auspicious Dates")
    st.write(", ".join(map(str, data["auspicious"])))

    st.subheader("Inauspicious Dates")
    st.write(", ".join(map(str, data["inauspicious"])))

else:
    st.warning("Monthly horoscope not generated yet. Run monthly generator first.")