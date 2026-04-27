# import sqlite3
# import json
# from datetime import date
# from openai import OpenAI
# from dotenv import load_dotenv
# import hashlib
# import os

# # ===============================
# # Load API Key
# # ===============================
# load_dotenv()

# api_key = os.getenv("API_KEY")

# if not api_key:
#     raise ValueError("API key not found. Check .env file")

# client = OpenAI(api_key=api_key)

# # ===============================
# # Zodiac list
# # ===============================
# ZODIACS = [
#     "Aries","Taurus","Gemini","Cancer","Leo","Virgo",
#     "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"
# ]

# COLORS = [
#     "Red", "Blue", "Green", "Yellow", "White",
#     "Pink", "Orange", "Purple", "Brown", "Grey",
#     "Gold", "Silver"
# ]

# def get_daily_lucky(sign, date_str):
#     key = sign + date_str
#     h = hashlib.md5(key.encode()).hexdigest()

#     color_index = int(h[:2], 16) % len(COLORS)
#     lucky_number = (int(h[2:6], 16) % 9) + 1

#     return COLORS[color_index], lucky_number

# # ===============================
# # Database setup
# # ===============================
# conn = sqlite3.connect("daily_horoscope.db")
# cursor = conn.cursor()

# cursor.execute("""
# CREATE TABLE IF NOT EXISTS daily_horoscope (
# date TEXT,
# zodiac_sign TEXT,
# general TEXT,
# career TEXT,
# love TEXT,
# finance TEXT,
# health TEXT,
# lucky_color TEXT,
# lucky_number INTEGER,
# PRIMARY KEY (date, zodiac_sign)
# )
# """)

# today = str(date.today())

# # Check if already generated
# cursor.execute("SELECT COUNT(*) FROM daily_horoscope WHERE date=?", (today,))
# if cursor.fetchone()[0] == 12:
#     print("Today's horoscope already exists.")
#     conn.close()
#     exit()

# # ===============================
# # Generate Function
# # ===============================
# def generate_daily(sign):
#     prompt = f"""
# Date: {today}
# Moon is in {ZODIACS}.

# Generate a DAILY horoscope for {sign}.

# Return ONLY valid JSON:
# {{
# "general": "",
# "career": "",
# "love": "",
# "finance": "",
# "health": "",
# "lucky_color": "",
# "lucky_number": 0
# }}
# """

#     response = client.chat.completions.create(
#         model="gpt-4o-mini",
#         messages=[{"role": "user", "content": prompt}],
#         temperature=0.7
#     )

#     text = response.choices[0].message.content.strip()

#     # Fix if model adds extra text
#     try:
#         data = json.loads(text)
#     except:
#         text = text[text.find("{"):text.rfind("}")+1]
#         data = json.loads(text)

#     return data

# # ===============================
# # Generate for all signs
# # ===============================
# for sign in ZODIACS:
#     print(f"Generating for {sign}...")
#     data = generate_daily(sign)

#     cursor.execute("""
#     INSERT OR REPLACE INTO daily_horoscope
#     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
#     """, (
#         today,
#         sign,
#         data["general"],
#         data["career"],
#         data["love"],
#         data["finance"],
#         data["health"],
#         "lucky_color",
#         "lucky_number"
#     ))

# conn.commit()
# conn.close()

# print("Daily horoscope generated for all signs.")

