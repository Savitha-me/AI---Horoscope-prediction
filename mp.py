import streamlit as st
import sqlite3
import json
from datetime import date

# Page settings
st.set_page_config(page_title="Monthly Horoscope", layout="wide")

st.title("🔮 Monthly Horoscope Viewer")

# Zodiac list
ZODIACS = [
    "Aries","Taurus","Gemini","Cancer","Leo","Virgo",
    "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"
]

# Current month/year
today = date.today()
year = today.year
month = today.month

# Zodiac selection
selected_sign = st.selectbox("Select Zodiac Sign", ZODIACS)

# Connect database
conn = sqlite3.connect("monthly_horoscope.db")
cursor = conn.cursor()

cursor.execute("""
SELECT general, love, finance, career, business, health, student,
       auspicious_dates, inauspicious_dates
FROM monthly_horoscope
WHERE year=? AND month=? AND zodiac_sign=?
""", (year, month, selected_sign))

result = cursor.fetchone()
conn.close()

if result:
    general, love, finance, career, business, health, student, good_days, bad_days = result

    good_days = json.loads(good_days)
    bad_days = json.loads(bad_days)

    st.subheader(f"{selected_sign} - {month}/{year}")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### General")
        st.write(general)

        st.markdown("### Love & Relationships")
        st.write(love)

        st.markdown("### Finance")
        st.write(finance)

        st.markdown("### Career")
        st.write(career)

    with col2:
        st.markdown("### Business")
        st.write(business)

        st.markdown("### Health")
        st.write(health)

        st.markdown("### Student")
        st.write(student)

        st.markdown("### 🌟 Auspicious Dates")
        st.write(", ".join(map(str, good_days)))

        st.markdown("### ⚠️ Inauspicious Dates")
        st.write(", ".join(map(str, bad_days)))

else:
    st.warning("Monthly horoscope not generated yet. Run the monthly generation script first.")