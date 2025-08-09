import streamlit as st
from PIL import Image, ImageDraw, ImageFont

# Party codes and colors
PARTIES = [
    ("S", "red"),
    ("SD", "gold"),
    ("V", "darkred"),
    ("C", "green"),
    ("L", "blue"),
    ("M", "navy"),
    ("KD", "darkblue"),
    ("MP", "limegreen"),
]

# Initialize state
if "alliances" not in st.session_state:
    st.session_state.alliances = []

def draw_parties(alliances):
    size = 100
    spacing = 10
    img = Image.new("RGB", (size * len(PARTIES) + spacing * (len(PARTIES)-1), size), "white")
    draw = ImageDraw.Draw(img)
    fnt = ImageFont.load_default()

    # Draw squares
    for i, (code, color) in enumerate(PARTIES):
        x0 = i * (size + spacing)
        y0 = 0
        draw.rectangle([x0, y0, x0+size, y0+size], fill=color, outline="black", width=2)
        bbox = draw.textbbox((0, 0), code, font=fnt)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        draw.text((x0 + (size - w)/2, y0 + (size - h)/2), code, fill="white", font=fnt)

    # Draw alliances
    for (p1, p2, idx) in alliances:
        if p1 in dict(PARTIES) and p2 in dict(PARTIES):
            i1 = [c for c, _ in PARTIES].index(p1)
            i2 = [c for c, _ in PARTIES].index(p2)
            x1 = i1 * (size + spacing) + size
            x2 = i2 * (size + spacing)
            mid_x = (x1 + x2) / 2
            y = size / 2 - 10
            draw.rectangle([mid_x - 15, y, mid_x + 15, y + 20], fill="white", outline="black")
            t = str(idx)
            tb = draw.textbbox((0, 0), t, font=fnt)
            tw = tb[2] - tb[0]
            th = tb[3] - tb[1]
            draw.text((mid_x - tw/2, y + (20 - th)/2), t, fill="black", font=fnt)

    return img

st.title("Alliance Map")

col1, col2 = st.columns(2)
with col1:
    p1 = st.selectbox("Party 1", ["Choose Party"] + [c for c, _ in PARTIES])
with col2:
    p2 = st.selectbox("Party 2", ["Choose Party"] + [c for c, _ in PARTIES])

if st.button("Strengthen Alliance"):
    if p1 == "Choose Party" or p2 == "Choose Party" or p1 == p2:
        st.error("Please choose two different parties.")
    else:
        current_indices = [idx for a1, a2, idx in st.session_state.alliances if {a1, a2} == {p1, p2}]
        next_idx = max(current_indices, default=0) + 1
        st.session_state.alliances.append((p1, p2, next_idx))

if st.button("Weaken Alliance"):
    if p1 == "Choose Party" or p2 == "Choose Party" or p1 == p2:
        st.error("Please choose two different parties with an alliance.")
    else:
        matches = [(a1, a2, idx) for (a1, a2, idx) in st.session_state.alliances if {a1, a2} == {p1, p2}]
        if not matches:
            st.error("No alliance exists between these parties.")
        else:
            to_remove = max(matches, key=lambda x: x[2])
            st.session_state.alliances.remove(to_remove)

st.image(draw_parties(st.session_state.alliances), caption="Current alliances")
