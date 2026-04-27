import streamlit as st
import sqlite3
from datetime import date

st.title("Daily Horoscope")

ZODIACS = [
    "Aries","Taurus","Gemini","Cancer","Leo","Virgo",
    "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"
]

sign = st.selectbox("Select Zodiac Sign", ZODIACS)

today = str(date.today())

def get_daily(sign):
    conn = sqlite3.connect("daily_horoscope.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT general, career, love, finance, health,
           lucky_color, lucky_number
    FROM daily_horoscope
    WHERE date=? AND zodiac_sign=?
    """, (today, sign))

    data = cursor.fetchone()
    conn.close()
    return data

data = get_daily(sign)

if data:
    st.header(f"{sign} Horoscope - {today}")

    st.subheader("General")
    st.write(data[0])

    st.subheader("Career & Business")
    st.write(data[1])

    st.subheader("Love & Relationships")
    st.write(data[2])

    st.subheader("Money & Finances")
    st.write(data[3])

    st.subheader("Health")
    st.write(data[4])

    st.success(f"Lucky Color: {data[5]}")
    st.success(f"Lucky Number: {data[6]}")
else:
    st.warning("Today's horoscope not generated yet. Run generate_daily.py first.")