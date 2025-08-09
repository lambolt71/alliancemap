
import streamlit as st
from PIL import Image, ImageDraw, ImageFont

# --- Configuration ---
PARTIES = [
    ("S", "red"),
    ("V", "darkred"),
    ("C", "green"),
    ("L", "blue"),
    ("M", "navy"),
    ("KD", "purple"),
    ("SD", "gold"),
    ("MP", "lightgreen")
]

# State initialization
if "alliances" not in st.session_state:
    st.session_state.alliances = []  # list of (party1, party2, index)
    st.session_state.next_index = 1

st.title("Alliance Builder")

# Draw the grid of parties
def draw_parties(alliances):
    size = 100
    spacing = 10
    img = Image.new("RGB", (size * len(PARTIES) + spacing * (len(PARTIES)-1), size), "white")
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default()
    
    # Draw squares
    for i, (code, color) in enumerate(PARTIES):
        x0 = i * (size + spacing)
        y0 = 0
        draw.rectangle([x0, y0, x0+size, y0+size], fill=color, outline="black", width=2)
        w, h = draw.textsize(code, font=font)
        draw.text((x0 + (size-w)/2, y0 + (size-h)/2), code, fill="white", font=font)
    
    # Draw alliances as white strips with index numbers
    for (p1, p2, idx) in alliances:
        if p1 in dict(PARTIES) and p2 in dict(PARTIES):
            i1 = [c for c, _ in PARTIES].index(p1)
            i2 = [c for c, _ in PARTIES].index(p2)
            x1 = i1 * (size + spacing) + size
            x2 = i2 * (size + spacing)
            mid_x = (x1 + x2) / 2
            y = size / 2 - 10
            draw.rectangle([mid_x - 15, y, mid_x + 15, y + 20], fill="white", outline="black")
            w, h = draw.textsize(str(idx), font=font)
            draw.text((mid_x - w/2, y + (20-h)/2), str(idx), fill="black", font=font)
    
    return img

# Display alliances
st.image(draw_parties(st.session_state.alliances), caption="Current alliances")

# --- Strengthen Alliance ---
st.header("Strengthen Alliance")
col1, col2 = st.columns(2)
with col1:
    p1 = st.selectbox("Party 1", ["Choose Party"] + [p[0] for p in PARTIES], key="strength_p1")
with col2:
    p2 = st.selectbox("Party 2", ["Choose Party"] + [p[0] for p in PARTIES], key="strength_p2")

if st.button("Strengthen Alliance"):
    if p1 == "Choose Party" or p2 == "Choose Party" or p1 == p2:
        st.warning("Please choose two different parties.")
    else:
        st.session_state.alliances.append((p1, p2, st.session_state.next_index))
        st.session_state.next_index += 1

# --- Weaken Alliance ---
st.header("Weaken Alliance")
col3, col4 = st.columns(2)
with col3:
    w1 = st.selectbox("Party 1", ["Choose Party"] + [p[0] for p in PARTIES], key="weaken_p1")
with col4:
    w2 = st.selectbox("Party 2", ["Choose Party"] + [p[0] for p in PARTIES], key="weaken_p2")

if st.button("Weaken Alliance"):
    if w1 == "Choose Party" or w2 == "Choose Party" or w1 == w2:
        st.warning("Please choose two different parties with an alliance.")
    else:
        # Find newest alliance between them
        matches = [(a, i) for i, a in enumerate(st.session_state.alliances) if {a[0], a[1]} == {w1, w2}]
        if not matches:
            st.warning("No alliance exists between these parties.")
        else:
            newest_idx = max(matches, key=lambda m: m[0][2])[1]
            st.session_state.alliances.pop(newest_idx)

# Refresh display
st.image(draw_parties(st.session_state.alliances), caption="Updated alliances")
