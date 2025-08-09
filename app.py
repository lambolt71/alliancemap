
import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from collections import defaultdict, deque

# ---------------------------
# Party palette
# ---------------------------
PARTIES = [
    ("S",  "#ef9a9a"),
    ("SD", "#fff59d"),
    ("V",  "#f06292"),
    ("C",  "#4caf50"),
    ("L",  "#81d4fa"),
    ("M",  "#1e3a8a"),
    ("KD", "#7c3aed"),
    ("G",  "#a5d6a7"),
]

PARTY_CODES = [p[0] for p in PARTIES]
PARTY_COLOR = {p: c for p, c in PARTIES}

SQUARE = 100
GAP = 14
PAD = 20
STRIP_LEN = int(SQUARE * 0.5)
STRIP_THK = int(SQUARE * 0.25)

def font(size=24):
    try:
        return ImageFont.truetype("arial.ttf", size)
    except:
        return ImageFont.load_default()

# ---------------------------
# Session state + compatibility shim
# ---------------------------
def _init_state():
    # New canonical shape: defaultdict(list) mapping frozenset({A,B}) -> [indices]
    if "alliances" not in st.session_state:
        st.session_state.alliances = defaultdict(list)
    else:
        # If an older app version stored alliances as a list of tuples,
        # migrate it to the new dict form so .items() works.
        if isinstance(st.session_state.alliances, list):
            migrated = defaultdict(list)
            for tup in st.session_state.alliances:
                # Expect (a,b,idx); ignore malformed items gracefully
                if isinstance(tup, (tuple, list)) and len(tup) == 3:
                    a, b, idx = tup
                    migrated[frozenset({a, b})].append(int(idx))
            st.session_state.alliances = migrated

    # Unified counter key
    if "next_idx" not in st.session_state:
        # Support old 'next_index' if present
        if "next_index" in st.session_state and isinstance(st.session_state.next_index, int):
            st.session_state.next_idx = st.session_state.next_index
        else:
            # derive from existing alliances
            max_idx = 0
            for lst in st.session_state.alliances.values():
                if lst:
                    max_idx = max(max_idx, max(lst))
            st.session_state.next_idx = max_idx + 1

_init_state()

# ---------------------------
# Helpers
# ---------------------------
def draw_palette_row():
    """Top row: show all 8 squares as a palette (no alliances drawn here)."""
    w = PAD*2 + len(PARTIES)*SQUARE + (len(PARTIES)-1)*GAP
    h = PAD*2 + SQUARE
    img = Image.new("RGB", (w, h), "white")
    d = ImageDraw.Draw(img)
    f = font(22)
    for i, (code, color) in enumerate(PARTIES):
        x = PAD + i*(SQUARE+GAP)
        y = PAD
        d.rectangle([x, y, x+SQUARE, y+SQUARE], fill=color, outline="black", width=2)
        tb = d.textbbox((0,0), code, font=f); tw = tb[2]-tb[0]; th = tb[3]-tb[1]
        d.text((x + SQUARE/2 - tw/2, y + SQUARE/2 - th/2), code, font=f, fill="black")
    return img

def connected_components(edges):
    """Return list of sets (nodes) for each connected component and adjacency map."""
    adj = defaultdict(set)
    nodes = set()
    for fs in edges:
        a,b = tuple(fs)
        nodes.add(a); nodes.add(b)
        adj[a].add(b); adj[b].add(a)
    seen = set()
    comps = []
    for n in nodes:
        if n in seen: continue
        comp = set()
        q = deque([n]); seen.add(n)
        while q:
            u = q.popleft(); comp.add(u)
            for v in adj[u]:
                if v not in seen:
                    seen.add(v); q.append(v)
        comps.append(comp)
    return comps, adj

def linearize_component(nodes, adj):
    """Simple left-to-right order. Prefer a path starting at degree-1 node."""
    if not nodes:
        return []
    deg1 = [n for n in nodes if len(adj[n]) == 1]
    start = deg1[0] if deg1 else next(iter(nodes))
    order, seen = [], set()
    cur = start
    while cur is not None:
        order.append(cur); seen.add(cur)
        nxt = next((v for v in adj[cur] if v not in seen), None)
        cur = nxt
    for n in nodes:
        if n not in seen:
            order.append(n); seen.add(n)
    return order

def draw_component_row(order, alliance_map):
    """Draw one connected component as a row of squares; draw strips for adjacent allied pairs."""
    n = len(order)
    if n == 0:
        return Image.new("RGB", (1,1), "white")
    w = PAD*2 + n*SQUARE + (n-1)*GAP
    h = PAD*2 + SQUARE
    img = Image.new("RGB", (w, h), "white")
    d = ImageDraw.Draw(img)
    f = font(22)

    pos = {}
    for i, code in enumerate(order):
        x = PAD + i*(SQUARE+GAP); y = PAD
        pos[code] = (x,y)
        d.rectangle([x, y, x+SQUARE, y+SQUARE], fill=PARTY_COLOR[code], outline="black", width=2)
        tb = d.textbbox((0,0), code, font=f); tw = tb[2]-tb[0]; th = tb[3]-tb[1]
        d.text((x + SQUARE/2 - tw/2, y + SQUARE/2 - th/2), code, font=f, fill="black")

    f_small = font(18)
    for i in range(n-1):
        a = order[i]; b = order[i+1]
        fs = frozenset({a,b})
        idxs = alliance_map.get(fs, [])
        if not idxs: continue
        x_a, y = pos[a]
        mx = x_a + SQUARE + GAP/2
        my = y + SQUARE/2
        x0 = mx - STRIP_LEN/2; y0 = my - STRIP_THK/2
        x1 = mx + STRIP_LEN/2; y1 = my + STRIP_THK/2
        d.rectangle([x0, y0, x1, y1], fill="white", outline="black")
        text = ",".join(str(i) for i in sorted(idxs))
        tb = d.textbbox((0,0), text, font=f_small); tw = tb[2]-tb[0]; th = tb[3]-tb[1]
        d.text(((x0+x1)/2 - tw/2, (y0+y1)/2 - th/2), text, font=f_small, fill="black")
    return img

def compose_components_image(components, adj, alliance_map):
    rows = []
    for comp in components:
        order = linearize_component(comp, adj)
        rows.append(draw_component_row(order, alliance_map))

    if not rows:
        return Image.new("RGB", (600, 100), "white")

    gap_v = 20
    width = max(r.width for r in rows)
    height = sum(r.height for r in rows) + gap_v*(len(rows)-1)
    canvas = Image.new("RGB", (width, height), "white")
    y = 0
    for r in rows:
        canvas.paste(r, (0, y))
        y += r.height + gap_v
    return canvas

# ---------------------------
# UI
# ---------------------------
st.set_page_config(page_title="Alliance Map", layout="centered")
st.title("Alliance Map")

col1, col2 = st.columns(2)
with col1:
    p1 = st.selectbox("Party 1", ["Choose Party"] + PARTY_CODES, key="p1")
with col2:
    p2 = st.selectbox("Party 2", ["Choose Party"] + PARTY_CODES, key="p2")

c1, c2 = st.columns(2)
with c1:
    if st.button("Strengthen Alliance"):
        if st.session_state.p1 == "Choose Party" or st.session_state.p2 == "Choose Party":
            st.error("Please choose two parties.")
        elif st.session_state.p1 == st.session_state.p2:
            st.error("Please choose two different parties.")
        else:
            fs = frozenset({st.session_state.p1, st.session_state.p2})
            next_idx = st.session_state.next_idx
            st.session_state.alliances[fs].append(next_idx)
            st.session_state.next_idx += 1
with c2:
    if st.button("Weaken Alliance"):
        if st.session_state.p1 == "Choose Party" or st.session_state.p2 == "Choose Party":
            st.error("Please choose two parties with an alliance.")
        elif st.session_state.p1 == st.session_state.p2:
            st.error("Please choose two different parties with an alliance.")
        else:
            fs = frozenset({st.session_state.p1, st.session_state.p2})
            if not st.session_state.alliances.get(fs):
                st.error("No alliance exists between those parties.")
            else:
                latest = max(st.session_state.alliances[fs])
                st.session_state.alliances[fs].remove(latest)
                if not st.session_state.alliances[fs]:
                    del st.session_state.alliances[fs]
                st.success(f"Removed newest alliance #{latest}.")

st.subheader("Party palette (reference)")
st.image(draw_palette_row(), use_column_width=False)

# Build alliances graph (only pairs that have any indices)
edges = {fs for fs, idxs in st.session_state.alliances.items() if idxs}
components, adj = connected_components(edges)

st.subheader("Alliance map (only connected parties)")
if not edges:
    st.info("No alliances yet. Strengthen an alliance to see the map.")
else:
    alliance_img = compose_components_image(components, adj, st.session_state.alliances)
    st.image(alliance_img, caption="Current alliances", use_column_width=False)

with st.sidebar:
    st.header("Alliances (by pair)")
    if not edges:
        st.write("—")
    else:
        for fs in sorted(st.session_state.alliances.keys(), key=lambda x: sorted(list(x))):
            st.write(f"{tuple(fs)}: {sorted(st.session_state.alliances[fs])}")
    if st.button("Reset"):
        st.session_state.alliances = defaultdict(list)
        st.session_state.next_idx = 1
        st.rerun()
