import streamlit as st
import sqlite3
import json
from datetime import date

# --------------------------------------------------
# Page Settings
# --------------------------------------------------
st.set_page_config(page_title="Horoscope Dashboard", layout="wide")
st.title("🔮 Horoscope Dashboard")

# Zodiac List
ZODIACS = [
    "Aries","Taurus","Gemini","Cancer","Leo","Virgo",
    "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"
]

# Mode Selection
mode = st.sidebar.radio(
    "Select Prediction Type",
    ["Daily Horoscope", "Monthly Horoscope"]
)

selected_sign = st.sidebar.selectbox("Select Zodiac Sign", ZODIACS)

today = date.today()
today_str = str(today)
year = today.year
month = today.month

# ==================================================
# DAILY HOROSCOPE
# ==================================================
def get_daily(sign):
    conn = sqlite3.connect("daily_horoscope.db")
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


# ==================================================
# MONTHLY HOROSCOPE
# ==================================================
def get_monthly(sign):
    conn = sqlite3.connect("monthly_horoscope.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT general, love, finance, career, business, health, student,
           auspicious_dates, inauspicious_dates
    FROM monthly_horoscope
    WHERE year=? AND month=? AND zodiac_sign=?
    """, (year, month, sign))

    data = cursor.fetchone()
    conn.close()
    return data


# ==================================================
# DISPLAY SECTION
# ==================================================

# ---------------- DAILY ----------------
if mode == "Daily Horoscope":
    st.header(f"📅 Daily Horoscope - {today_str}")

    data = get_daily(selected_sign)

    if data:
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("General")
            st.write(data[0])

            st.subheader("Career & Business")
            st.write(data[1])

            st.subheader("Love & Relationships")
            st.write(data[2])

        with col2:
            st.subheader("Money & Finances")
            st.write(data[3])

            st.subheader("Health")
            st.write(data[4])

            st.success(f"Lucky Color: {data[5]}")
            st.success(f"Lucky Number: {data[6]}")
    else:
        st.warning("Today's horoscope not generated yet. Run daily generation script.")


# ---------------- MONTHLY ----------------
else:
    st.header(f"📆 Monthly Horoscope - {month}/{year}")

    data = get_monthly(selected_sign)

    if data:
        general, love, finance, career, business, health, student, good_days, bad_days = data

        good_days = json.loads(good_days)
        bad_days = json.loads(bad_days)

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("General")
            st.write(general)

            st.subheader("Love & Relationships")
            st.write(love)

            st.subheader("Finance")
            st.write(finance)

            st.subheader("Career")
            st.write(career)

        with col2:
            st.subheader("Business")
            st.write(business)

            st.subheader("Health")
            st.write(health)

            st.subheader("Student")
            st.write(student)

            st.markdown("### 🌟 Auspicious Dates")
            st.write(", ".join(map(str, good_days)))

            st.markdown("### ⚠️ Inauspicious Dates")
            st.write(", ".join(map(str, bad_days)))

    else:
        st.warning("Monthly horoscope not generated yet. Run monthly generation script.")