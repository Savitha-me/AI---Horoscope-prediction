import streamlit as st
import sqlite3
from datetime import date
import os

# ======================================================
# CONFIG
# ======================================================
DB_FILE = "monthly_article_tamil.db"

ZODIACS = ["மேஷம்","ரிஷபம்","மிதுனம்","கடகம்","சிம்மம்","கன்னி",
        "துலாம்","விருச்சிகம்","தனுசு","மகரம்","கும்பம்","மீனம்"
]
# ======================================================
# TAMIL POOJA LINKS (Monthly change)
# ======================================================
import hashlib

POOJA_LINKS = {
    "நவகிரக பூஜை": "https://www.astroved.com/temple/navagraha-pooja",
    "மகாலட்சுமி பூஜை": "https://www.astroved.com/temple/mahalakshmi",
    "கணபதி பூஜை": "https://www.astroved.com/temple/ganesha",
    "சனி பகவான் பூஜை": "https://www.astroved.com/temple/saturn",
    "செவ்வாய் தோஷ நிவாரண பூஜை": "https://www.astroved.com/temple/mars",
    "சந்திர பூஜை": "https://www.astroved.com/temple/moon",
    "சூரிய நமஸ்கார பூஜை": "https://www.astroved.com/temple/sun",
    "சுக்ரன் பூஜை": "https://www.astroved.com/temple/venus",
    "குரு பகவான் பூஜை": "https://www.astroved.com/temple/jupiter",
    "துர்கை அம்மன் பூஜை": "https://www.astroved.com/temple/durga"
}

TAMIL_POOJAS = list(POOJA_LINKS.keys())

def get_section_pooja_tamil(sign, section):
    """
    Monthly stable pooja for each section.
    Changes automatically next month.
    """
    key = f"{sign}_{section}_{year}_{month}"
    h = hashlib.md5(key.encode()).hexdigest()
    index = int(h[:8], 16) % len(TAMIL_POOJAS)
    name = TAMIL_POOJAS[index]
    return name, POOJA_LINKS[name]

today      = date.today()
year       = today.year
month      = today.month
month_name = today.strftime("%B")

# ======================================================
# FETCH ARTICLE
# ======================================================
def fetch_tamil_article(sign):
    if not os.path.exists(DB_FILE):
        st.error("Database file not found")
        return None

    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    # Fetch latest available article for the sign
    cur.execute("""
        SELECT article_text, year, month
        FROM monthly_articles_tamil
        WHERE zodiac_sign=?
        ORDER BY year DESC, month DESC
        LIMIT 1
    """, (sign,))

    row = cur.fetchone()
    conn.close()

    if row:
        article_text, y, m = row
        st.caption(f"{sign} – {m}/{y}")
        return article_text

    return None

# ======================================================
# WORD COUNT
# ======================================================
def count_words(text):
    return len(text.split())

# ======================================================
# DISPLAY ARTICLE (Keeps structure)
# ======================================================
def display_article(sign, text):
    if not text:
        st.error("Article content is empty")
        return

    lines = text.split("\n")

    current_h2 = None
    section_buffer = []
    content_found = False

    def flush_section():
        nonlocal section_buffer, content_found

        if not section_buffer:
            return

        content_found = True

        for ln in section_buffer:
            s = ln.strip()
            if not s:
                continue

            # Heading 3
            if s.startswith("Heading 3:"):
                st.markdown(f"### {s.replace('Heading 3:', '').strip()}")
            else:
                st.write(s)

        # Show section pooja only if H2 exists
        if current_h2:
            name, link = get_section_pooja_tamil(sign, current_h2)
            st.markdown(
                f"""
                🪔 **{current_h2} – பரிந்துரைக்கப்படும் பூஜை**  
                [{name}]({link})
                """
            )

        section_buffer = []

    for line in lines:
        s = line.strip()
        if not s:
            continue

        # Heading 1
        if s.startswith("Heading 1:"):
            flush_section()
            title = s.replace("Heading 1:", "").strip()
            st.markdown(f"# {title}")

        # Heading 2
        elif s.startswith("Heading 2:"):
            flush_section()
            current_h2 = s.replace("Heading 2:", "").strip()
            st.markdown(f"## {current_h2}")

        else:
            section_buffer.append(s)

    flush_section()

    # If no headings detected, show full article directly
    if not content_found:
        st.warning("Heading format not detected. Showing full article.")
        st.write(text)
# ======================================================
# UI
# ======================================================
st.set_page_config(layout="wide")
st.title("🔮 Tamil Monthly Horoscope Articles")

# Zodiac selector
sign = st.selectbox("ராசியை தேர்வு செய்யவும் (Select Zodiac)", ZODIACS)

article = fetch_tamil_article(sign)

if article:
    st.caption(f"{sign} – {month_name} {year}")

    # Word count display
    words = count_words(article)
    st.info(f"Total Words: {words}")

    if words < 800:
        st.warning("Article length is below expected (800+).")

    st.markdown("---")
    display_article(sign, article)
else:
    st.error("Tamil article not found.")
    st.info("Run your generator first:\n\npython monthly_article_tamil_generator.py")

