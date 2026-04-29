**AI Horoscope Personalization engine**
An AI-powered horoscope platform built with OpenAI GPT and FastAPI. 
It generates daily and monthly horoscope predictions for all 12 zodiac signs in both English and Tamil, with pooja recommendations, lucky color/number, 
auspicious dates, and FAQs — 
all stored in SQLite and served via a Streamlit.

**Features**
**Daily Prediction**

5 sections — General, Career, Love, Finance, Health 
Lucky Color — Deterministic per sign per date using MD5 hash 
Lucky Number — Deterministic per sign per date
2 Pooja Recommendations — AI picks 2 poojas from astroved website with specific reasons based on the day's prediction
8 FAQs — AI-generated Q&A grounded in today's horoscope themes
Duplicate prevention — skips generation if today's data already exists

**Monthly Prediction**

7 sections — General, Love, Finance, Career, Business, Health, Student
Auspicious Dates — 4–6 lucky dates for the month
Inauspicious Dates — 3–5 dates to be cautious
Planetary Transits — Jupiter, Saturn, Mercury retrograde considered
10 FAQs — Monthly themed Q&A per sign
Divine technique appended to each section

**Tamil Articles**

Full monthly article in Tamil per zodiac sign
Each section has 2 paragraphs:

Paragraph 1 — Translated from English prediction
Paragraph 2 — Freshly generated original Tamil content


Foreign script characters automatically cleaned
Parsed into structured heading/content format in API response
