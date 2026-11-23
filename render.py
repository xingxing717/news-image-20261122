#!/usr/bin/env python3
"""Render the 22 November 2026 front page: one 1024x1024 PNG.

Deterministic: pure Pillow vector drawing + fixed strings, no timestamps,
no network, no random numbers. Run twice -> byte-identical entry.png.
"""
import hashlib
import os
import textwrap
from PIL import Image, ImageDraw, ImageFont

W = H = 1024
M = 28  # margin

PAPER = (246, 241, 230)
INK = (25, 23, 19)
GREY = (92, 86, 76)
RED = (179, 39, 30)
TEAL = (14, 107, 107)
BLUE = (29, 78, 137)
GOLD = (176, 124, 0)
GREEN = (46, 125, 50)
RULE = (25, 23, 19)
HAIR = (190, 182, 168)

F_SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
F_SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
F_SANS_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def font(path, size):
    return ImageFont.truetype(path, size)


def wrap(d, text, f, width):
    """Greedy word wrap by measured pixel width."""
    words = text.split()
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if d.textlength(trial, font=f) <= width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


# ---------------------------------------------------------------- stories
# Every item happened, or was first reported, on Sunday 22 November 2026
# (sources: Reuters/AP/AFP/BBC/Euronews/ESA wires and Sunday round-ups).
HEADLINE = {
    "kicker": "CLIMATE  ·  ANTALYA, TURKEY  —  THE LONGEST COP ON RECORD",
    "title": "COP31 COLLAPSES",
    "deck": ("The EU rejects a final draft with no mention of fossil fuels, and "
             "nearly 200 nations leave Antalya with no deal after two days "
             "of overtime."),
    "chips": ["44 HRS OVERTIME", "c. 200 NATIONS", "$142M PLEDGED"],
}

SECTIONS = [
    ("MIDDLE EAST & GULF", RED, [
        ("Iran hits US bases in Bahrain",
         "Missiles and drones strike an industrial site; two people hurt as Gulf states condemn the attack."),
        ("Tankers in the crossfire",
         "At least three oil tankers are struck or damaged near the Strait of Hormuz."),
        ("Hormuz 'not difficult' to reopen",
         "Iran's foreign minister says reopening hinges on the US accepting Tehran's conditions."),
        ("Gaza strikes go on",
         "Israeli strikes continue despite the ceasefire framework."),
        ("Settlers torch cars in West Bank",
         "Twelve vehicles are burned in four villages near Ramallah; Israel opens an inquiry."),
        ("Lebanon under pressure",
         "Israeli military pressure continues amid the Hezbollah disarmament dispute."),
    ]),
    ("EUROPE", BLUE, [
        ("Drone hits flats near Kyiv",
         "A Russian drone strikes a five-storey block in Dymer; 14 people are missing."),
        ("Kryvyi Rih missile kills two",
         "A 7-year-old boy and a 20-year-old woman are killed; 60 people are wounded."),
        ("Burning ship towed in the Baltic",
         "Finland tows the drone-hit Russian cargo ship Sparta II in the Gulf of Finland."),
        ("Germany tests kamikaze drones",
         "Berlin trials AI-targeted attack drones in Lithuania."),
        ("Spain: PP leads in the polls",
         "Conservatives run ahead of the PSOE a week before the 29 November election."),
    ]),
    ("ASIA–PACIFIC", TEAL, [
        ("Nepal PM lands in India",
         "Balendra Shah begins a two-day state visit for talks with Narendra Modi."),
        ("India–China border talks",
         "Commanders conclude a fresh round over the Arunachal frontier."),
        ("India 720/9 vs New Zealand",
         "The hosts declare with a 352-run lead in the Wellington Test."),
        ("Chahal joins the BJP",
         "The cricketer takes a National OBC Morcha executive post."),
        ("BJP MP dies at 72",
         "Ramrao Wadkute dies of a cardiac arrest at AIIMS, New Delhi."),
        ("Factory fire in Indonesia",
         "Three dead and 36 missing after a blaze at a candy plant in Cikande."),
        ("Mascot mania in Saitama",
         "Two hundred colourful characters take over Japan's mascot festival."),
    ]),
    ("AMERICAS", GREEN, [
        ("'El Chapo Isidro' captured",
         "Mexican special forces seize the cartel boss in Sinaloa; 11 are killed in the raid."),
        ("Democrats' big House win",
         "US Democrats secure their biggest House majority in decades."),
        ("FIFA to name UK hosts",
         "Football's governing body is set to confirm the UK for the 2035 Women's World Cup."),
        ("NWSL crown for KC Current",
         "Kansas City beat Washington Spirit, who lose a third straight final."),
        ("Thitikul's third in a row",
         "The Thai star wins a third successive CME Group Tour Championship."),
    ]),
    ("AFRICA", GOLD, [
        ("Drones hit Khartoum",
         "Strikes damage a UN building in Sudan's capital."),
        ("Blast at Benghazi port",
         "A suspected drone strike hits a Russian ship in Libya."),
        ("Morocco's upside-down park",
         "A surreal sculpture park turns the world upside down."),
    ]),
    ("SCIENCE & SPORT", (122, 63, 133), [
        ("BepiColombo glitch",
         "ESA reports a thruster software issue after the Mercury orbit entry."),
        ("Alcaraz takes Turin",
         "The Spaniard beats Zverev 6–2, 7–6(7) for a first ATP Finals title."),
        ("Márquez: eighth title",
         "The Ducati rider seals the MotoGP crown in Portugal, equalling Agostini."),
        ("Verstappen wins in Vegas",
         "A third Las Vegas Grand Prix win in four years."),
        ("Liverpool 4–0 Man Utd",
         "Pochettino's first match as United boss ends in an Anfield rout."),
        ("Price wins darts Grand Slam",
         "Gerwyn Price beats Gian van Veen 16–11 for a first major in four years."),
        ("Haugan wins Gurgl slalom",
         "Norway takes the top two places in Austria."),
    ]),
]

MARKETS = [
    ("S&P 500", "-3.7%", "6,910"),
    ("NIKKEI", "-5.06%", ""),
    ("BRENT CRUDE", "+0.57%", "$89.95"),
    ("FTSE 100", "-1.02%", "10,346"),
]

# Columns: (x0, x1, [section indices])
COLUMNS = [
    (M, 348, [0, 3]),        # Middle East & Gulf, Americas
    (356, 680, [1, 5]),      # Europe, Science & Sport
    (688, W - M, [2, 4]),    # Asia–Pacific, Africa
]


# ---------------------------------------------------------------- drawing
def draw_globe(d, cx, cy, r):
    """Flat vector globe: teal disc, latitude/longitude arcs, land blobs,
    red crack zigzag, small sun."""
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(23, 126, 130))
    # latitude arcs
    for k, rr in ((0.55, 0.45), (0.0, 0.30), (-0.55, 0.45)):
        y = cy + k * r
        w = (r * rr) * 2
        d.arc([cx - w / 2, y - 6, cx + w / 2, y + 6], 0, 180, fill=(246, 241, 230), width=3)
    # longitude arcs
    d.arc([cx - r * 0.45, cy - r, cx + r * 0.45, cy + r], 270, 90, fill=(246, 241, 230), width=3)
    d.arc([cx - r * 0.45, cy - r, cx + r * 0.45, cy + r], 90, 270, fill=(246, 241, 230), width=3)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(25, 23, 19), width=3)
    # land blobs (simple flat polygons)
    d.polygon([(cx - 52, cy - 30), (cx - 18, cy - 52), (cx + 2, cy - 28),
               (cx - 8, cy - 2), (cx - 40, cy - 6)], fill=(94, 168, 74))
    d.polygon([(cx + 8, cy + 12), (cx + 46, cy + 2), (cx + 56, cy + 30),
               (cx + 26, cy + 44), (cx + 2, cy + 30)], fill=(94, 168, 74))
    d.polygon([(cx - 58, cy + 34), (cx - 30, cy + 26), (cx - 22, cy + 48),
               (cx - 48, cy + 56)], fill=(94, 168, 74))
    # red crack across the globe
    crack = [(cx - 58, cy - 58), (cx - 30, cy - 34), (cx - 46, cy - 8),
             (cx - 12, cy + 12), (cx - 30, cy + 38), (cx + 4, cy + 58)]
    d.line(crack, fill=RED, width=5, joint="curve")
    # sun top-right
    sx, sy, sr = cx + r + 26, cy - r - 6, 16
    d.ellipse([sx - sr, sy - sr, sx + sr, sy + sr], fill=(232, 164, 32))
    for ang in range(0, 360, 45):
        import math
        a = math.radians(ang)
        x1, y1 = sx + (sr + 3) * math.cos(a), sy + (sr + 3) * math.sin(a)
        x2, y2 = sx + (sr + 10) * math.cos(a), sy + (sr + 10) * math.sin(a)
        d.line([x1, y1, x2, y2], fill=(232, 164, 32), width=3)


def wrap_mixed(d, segments, width):
    """Greedy wrap of [(text, font, color)] segments into lines of runs."""
    tokens = []
    for text, f, c in segments:
        for w in text.split(" "):
            tokens.append((w, f, c))
    lines, cur, cur_w = [], [], 0.0
    for w, f, c in tokens:
        ww = d.textlength(w, font=f)
        sp = d.textlength(" ", font=f) if cur else 0.0
        if cur and cur_w + sp + ww > width:
            lines.append(cur)
            cur, cur_w = [(w, f, c)], ww
        else:
            cur.append((w, f, c))
            cur_w += sp + ww
    if cur:
        lines.append(cur)
    return lines


def draw_mixed_line(d, x, y, line):
    cx = x
    for text, f, c in line:
        d.text((cx, y), text, font=f, fill=c)
        cx += d.textlength(text, font=f) + d.textlength(" ", font=f)
    return cx
def draw_section_icon(d, x, y, color, kind):
    """Tiny flat glyph in a coloured square, 22x22."""
    d.rectangle([x, y, x + 22, y + 22], fill=color)
    c = (246, 241, 230)
    if kind == "flame":  # Middle East
        d.polygon([(x + 11, y + 3), (x + 18, y + 12), (x + 15, y + 19),
                   (x + 7, y + 19), (x + 4, y + 12)], fill=c)
    elif kind == "globe":  # Europe
        d.ellipse([x + 4, y + 4, x + 18, y + 18], outline=c, width=2)
        d.line([x + 4, y + 11, x + 18, y + 11], fill=c, width=2)
    elif kind == "sun":  # Asia-Pacific
        d.ellipse([x + 7, y + 7, x + 15, y + 15], fill=c)
        for dx, dy in ((0, -4), (0, 4), (-4, 0), (4, 0)):
            d.line([x + 11 + dx, y + 11 + dy, x + 11 + dx * 1.6, y + 11 + dy * 1.6],
                   fill=c, width=2)
    elif kind == "star":  # Americas
        d.polygon([(x + 11, y + 3), (x + 13, y + 9), (x + 19, y + 9), (x + 14, y + 13),
                   (x + 16, y + 19), (x + 11, y + 15), (x + 6, y + 19),
                   (x + 8, y + 13), (x + 3, y + 9), (x + 9, y + 9)], fill=c)
    elif kind == "mount":  # Africa
        d.polygon([(x + 3, y + 19), (x + 9, y + 7), (x + 14, y + 14),
                   (x + 17, y + 9), (x + 20, y + 19)], fill=c)
    else:  # rocket — Science & Sport
        d.polygon([(x + 11, y + 2), (x + 16, y + 11), (x + 13, y + 18),
                   (x + 9, y + 18), (x + 6, y + 11)], fill=c)
        d.polygon([(x + 6, y + 12), (x + 3, y + 18), (x + 8, y + 16)], fill=c)
        d.polygon([(x + 16, y + 12), (x + 19, y + 18), (x + 14, y + 16)], fill=c)


ICON_KINDS = ["flame", "globe", "sun", "star", "mount", "rocket"]


def render():
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)

    # ---- masthead ----
    y = 22
    d.line([M, y, W - M, y], fill=RULE, width=3)
    y += 12
    f_mast = font(F_SERIF, 56)
    title = "THE WORLD IN ONE DAY"
    tw = d.textlength(title, font=f_mast)
    d.text(((W - tw) / 2, y), title, font=f_mast, fill=INK)
    y += 68
    n_stories = 1 + sum(len(s[2]) for s in SECTIONS)
    f_sub = font(F_SANS_B, 15)
    sub = (f"SUNDAY 22 NOVEMBER 2026   ·   {n_stories} STORIES   ·   7 REGIONS"
           f"   ·   ONE PAGE")
    tw = d.textlength(sub, font=f_sub)
    d.text(((W - tw) / 2, y), sub, font=f_sub, fill=RED)
    y += 28
    d.line([M, y, W - M, y], fill=RULE, width=2)
    d.line([M, y + 4, W - M, y + 4], fill=RULE, width=1)
    y += 14

    # ---- headline block ----
    hx0, hx1 = M, 648
    ix0, ix1 = 668, W - M
    f_kick = font(F_SANS_B, 14)
    d.text((hx0, y), HEADLINE["kicker"], font=f_kick, fill=RED)
    y += 24
    f_head = font(F_SERIF, 58)
    d.text((hx0, y), HEADLINE["title"], font=f_head, fill=INK)
    y += 74
    f_deck = font(F_SANS, 16)
    for line in wrap(d, HEADLINE["deck"], f_deck, hx1 - hx0):
        d.text((hx0, y), line, font=f_deck, fill=INK)
        y += 21
    y += 6
    f_chip = font(F_SANS_B, 12)
    cx = hx0
    for chip in HEADLINE["chips"]:
        cw = d.textlength(chip, font=f_chip) + 18
        d.rounded_rectangle([cx, y, cx + cw, y + 24], radius=12, fill=INK)
        d.text((cx + 9, y + 5), chip, font=f_chip, fill=PAPER)
        cx += cw + 8
    # headline illustration
    draw_globe(d, (ix0 + ix1) // 2 - 14, 208, 62)
    f_cap = font(F_SANS, 11)
    cap = "Antalya, Turkey — the summit ends with no deal."
    tw = d.textlength(cap, font=f_cap)
    d.text(((ix0 + ix1 - tw) / 2, 292), cap, font=f_cap, fill=GREY)

    y = 316
    d.line([M, y, W - M, y], fill=RULE, width=2)
    y += 10
    grid_top = y

    # ---- three-column grid ----
    f_sec = font(F_SANS_B, 13)
    f_t = font(F_SANS_B, 13)
    f_b = font(F_SANS, 11)
    col_bottom = 884
    for (x0, x1, secs) in COLUMNS:
        cy = grid_top
        for si in secs:
            name, color, stories = SECTIONS[si]
            # section header
            draw_section_icon(d, x0, cy, color, ICON_KINDS[si])
            d.rectangle([x0 + 28, cy, x1, cy + 22], fill=color)
            d.text((x0 + 36, cy + 4), name, font=f_sec, fill=(255, 255, 255))
            cy += 28
            for (t, b) in stories:
                lines = wrap_mixed(d, [(t + " —", f_t, INK), (b, f_b, GREY)],
                                   x1 - x0 - 14)
                d.text((x0, cy), "▪", font=f_t, fill=color)
                for line in lines:
                    draw_mixed_line(d, x0 + 14, cy, line)
                    cy += 14
                cy += 3
                d.line([x0, cy, x1, cy], fill=HAIR, width=1)
                cy += 5
            cy += 8
        # column rule
        d.line([x1 + 4, grid_top, x1 + 4, col_bottom], fill=HAIR, width=1)

    # ---- markets strip ----
    y = 896
    d.rectangle([M, y, W - M, y + 56], fill=INK)
    f_mt = font(F_SANS_B, 13)
    f_mv = font(F_SANS_B, 15)
    d.text((M + 14, y + 8), "MARKETS", font=f_mt, fill=(232, 164, 32))
    d.text((M + 14, y + 28), "AI SELL-OFF DEEPENS", font=font(F_SANS, 11),
           fill=(200, 192, 176))
    mx = M + 190
    step = (W - M - mx) // 4
    for (name, val, extra) in MARKETS:
        neg = val.startswith("-")
        col = (224, 92, 80) if neg else (120, 200, 120)
        d.text((mx, y + 8), name, font=f_mt, fill=(200, 192, 176))
        d.text((mx, y + 28), val + ("  " + extra if extra else ""),
               font=f_mv, fill=col)
        mx += step

    # ---- footer ----
    y = 966
    d.line([M, y, W - M, y], fill=RULE, width=1)
    f_f = font(F_SANS, 11)
    foot = ("Every story happened, or was first reported, on Sunday 22 November 2026  ·  "
            "Sources: Reuters · AP · AFP · BBC · Euronews · ESA")
    tw = d.textlength(foot, font=f_f)
    d.text(((W - tw) / 2, y + 8), foot, font=f_f, fill=GREY)

    out = os.environ.get("MAKEFUN_OUTPUT_DIR")
    path = os.path.join(out, "entry.png") if out else "entry.png"
    img.save(path, format="PNG")
    return path


if __name__ == "__main__":
    p = render()
    data = open(p, "rb").read()
    print(p, len(data), "bytes", hashlib.sha256(data).hexdigest())
