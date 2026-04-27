import streamlit as st
import sqlite3
import json
import random
from datetime import date

# --------------------------------------------------
# CONFIG
# --------------------------------------------------
DAILY_DB = "daily_horoscope.db"
MONTHLY_DB = "monthly_horoscope.db"
POOJA_FILE = "temple_links.json"

ZODIACS = [
    "Aries","Taurus","Gemini","Cancer","Leo","Virgo",
    "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"
]

today = date.today()
year = today.year
month = today.month
today_str = str(today)

st.set_page_config(page_title="Horoscope Portal", layout="wide")
st.title("🔮 AI Horoscope Portal")

# --------------------------------------------------
# LOAD POOJAS
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
# DATABASE FUNCTIONS
# --------------------------------------------------
def get_daily(sign):
    conn = sqlite3.connect(DAILY_DB)
    cursor = conn.cursor()

    cursor.execute("""
    SELECT general, career, love, finance, health,
           lucky_color, lucky_number
    FROM daily_horoscope
    WHERE date=? AND zodiac_sign=?
    """, (today_str, sign))

    data = cursor.fetchone()
    conn.close()
    return data


def get_monthly(sign):
    conn = sqlite3.connect(MONTHLY_DB)
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
# UI CONTROLS
# --------------------------------------------------
col1, col2 = st.columns([2, 1])

with col1:
    selected_sign = st.selectbox("Select Zodiac Sign", ZODIACS)

with col2:
    view_mode = st.radio("View", ["Daily", "Monthly"])

st.markdown("---")


# ==================================================
# DAILY VIEW
# ==================================================
if view_mode == "Daily":

    data = get_daily(selected_sign)

    if data:
        st.header(f"{selected_sign} Daily Horoscope - {today_str}")

        sections = [
            ("General", data[0]),
            ("Career", data[1]),
            ("Relationships", data[2]),
            ("Finances", data[3]),
            ("Health", data[4])
        ]

        tabs = st.tabs([s[0] for s in sections])

        for i, (title, content) in enumerate(sections):
            with tabs[i]:
                st.write(content)

                pooja_name, pooja_link = get_random_pooja()
                st.info(
                    f"Divine technique to improve your {title}: "
                    f"[{pooja_name}]({pooja_link})"
                )

        st.success(f"Lucky Color: {data[5]}")
        st.success(f"Lucky Number: {data[6]}")

    else:
        st.warning("Daily horoscope not generated yet.")


# ==================================================
# MONTHLY VIEW
# ==================================================
else:

    data = get_monthly(selected_sign)

    if data:
        st.header(f"{selected_sign} Monthly Horoscope - {month}/{year}")

        sections = [
            ("General", data["general"]),
            ("Relationships", data["love"]),
            ("Finances", data["finance"]),
            ("Career", data["career"]),
            ("Business", data["business"]),
            ("Health", data["health"]),
            ("Education", data["student"])
        ]

        # Tabs for monthly sections
        tabs = st.tabs([s[0] for s in sections])

        for i, (title, content) in enumerate(sections):
            with tabs[i]:
                with st.expander(f"View {title} Prediction", expanded=True):
                    st.write(content)

                    pooja_name, pooja_link = get_random_pooja()
                    st.info(
                        f"Divine technique to improve your {title}: "
                        f"[{pooja_name}]({pooja_link})"
                    )

        # Dates section
        st.markdown("---")
        colA, colB = st.columns(2)

        with colA:
            st.success(
                "Auspicious Dates: " +
                ", ".join(map(str, data["auspicious"]))
            )

        with colB:
            st.error(
                "Inauspicious Dates: " +
                ", ".join(map(str, data["inauspicious"]))
            )

    else:
        st.warning("Monthly horoscope not generated yet.")