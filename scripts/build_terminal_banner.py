#!/usr/bin/env python3
"""Generate the profile README hero banner (dark + light SVG).

Mirrors the "whoami.md" hero card from the alejandro-perez portfolio
(https://github.com/iolalo/portfolio) -- same file-tree sidebar, tab bar,
`~$ whoami` prompt and pill badges -- so the GitHub profile and the
portfolio site read as the same product.

Usage:
    python scripts/build_terminal_banner.py --photo assets/avatar.png \
        --out-dark assets/banner-dark.svg --out-light assets/banner-light.svg
"""
import argparse
import base64
import io
import textwrap

from PIL import Image

CANVAS_W, CANVAS_H = 1000, 420
TITLEBAR_H = 40
STATUSBAR_H = 26
SIDEBAR_W = 200
PAD = 26
AVATAR_SIZE = 108

SIDEBAR_TREE = [
    ("◆", "whoami.md", True),       # ◆
    ("▸", "experiencia/", False),   # ▸
    ("{ }", "skills.json", False),
    ("⇢", "proyectos.link", False),  # ⇢
    ("◆", "educacion.md", False),
    ("$", "contacto.sh", False),
]
BUILD_ITEM = ("↓", "CV_Alejandro_Perez.pdf")  # ↓

ROLE_LINE = "Senior BI Analyst · Power BI Developer · Data Modeling & Governance"
LEDE = (
    "Power BI ecosystem owner end-to-end — semantic modeling, "
    "advanced DAX, dynamic RLS, governance & CI/CD with Git."
)
BADGES = ["\U0001F4CD Buenos Aires, AR", "Star Schema", "Dynamic RLS", "Tabular Editor", "CI/CD + Git"]

MONO = "ui-monospace,SFMono-Regular,Consolas,monospace"
SANS = "ui-sans-serif,-apple-system,Segoe UI,Roboto,sans-serif"

THEMES = {
    "dark": {
        "bg": "#10141c",
        "panel": "#171d29",
        "panel2": "#1d2432",
        "sidebar": "#0d1119",
        "border": "#2a3242",
        "border_soft": "#212838",
        "text": "#e9e8e3",
        "text_dim": "#9aa4b8",
        "text_faint": "#5c6478",
        "gold": "#f2c811",
        "gold_dim": "#a6903f",
        "teal": "#01b8aa",
        "teal_dim": "#4fada6",
        "dot": "#3a4256",
    },
    "light": {
        "bg": "#f4f5f8",
        "panel": "#ffffff",
        "panel2": "#eef1f6",
        "sidebar": "#eaecf1",
        "border": "#d7dce6",
        "border_soft": "#e2e6ee",
        "text": "#1b2130",
        "text_dim": "#4b5468",
        "text_faint": "#838ca0",
        "gold": "#9c7a0a",
        "gold_dim": "#8a6b1f",
        "teal": "#027a70",
        "teal_dim": "#0a8f83",
        "dot": "#c7cddb",
    },
}


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def wrap(text, width):
    return textwrap.wrap(text, width=width) or [""]


def load_avatar_b64(photo_path):
    im = Image.open(photo_path).convert("RGB")
    w, h = im.size
    side = min(w, h)
    x0, y0 = (w - side) // 2, (h - side) // 2
    im = im.crop((x0, y0, x0 + side, y0 + side)).resize((AVATAR_SIZE * 2, AVATAR_SIZE * 2), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, format="JPEG", quality=82)
    return base64.b64encode(buf.getvalue()).decode("ascii")


def text_width(s, font_size, mono):
    return len(s) * font_size * (0.605 if mono else 0.52)


def badge_row(badges, x0, y_top, max_w, t):
    """Lay pill badges left-to-right, wrapping to a new row when out of width."""
    out = []
    x, y = x0, y_top
    row_h = 30
    pad_x = 10
    gap = 8
    for label in badges:
        w = text_width(label, 11.5, True) + pad_x * 2
        if x != x0 and x + w > x0 + max_w:
            x = x0
            y += row_h
        out.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="22" rx="11" '
            f'fill="{t["teal"]}" fill-opacity="0.08" stroke="{t["border"]}"/>'
            f'<text x="{x + w / 2:.1f}" y="{y + 15}" text-anchor="middle" fill="{t["teal_dim"]}" '
            f'font-family="{MONO}" font-size="11.5">{esc(label)}</text>'
        )
        x += w + gap
    return "".join(out), y + row_h


def build_svg(theme_name, avatar_b64):
    t = THEMES[theme_name]

    # ---- title bar --------------------------------------------------- #
    dots = "".join(f'<circle cx="{24 + i * 18}" cy="20" r="5.5" fill="{t["dot"]}"/>' for i in range(3))
    titlebar = f'''<rect width="{CANVAS_W}" height="{TITLEBAR_H}" fill="{t["sidebar"]}"/>
<path d="M0 {TITLEBAR_H}H{CANVAS_W}" stroke="{t["border"]}"/>
{dots}
<text x="66" y="25" font-family="{MONO}" font-size="12.5" fill="{t["text_faint"]}">
<tspan fill="{t["text_dim"]}" font-weight="600">alejandro-perez</tspan> — github · whoami.md</text>
<rect x="{CANVAS_W - 300}" y="9" width="150" height="22" rx="4" fill="none" stroke="{t["border"]}"/>
<text x="{CANVAS_W - 225}" y="24" text-anchor="middle" font-family="{MONO}" font-size="12" fill="{t["text_dim"]}">in/alejandroperez-data</text>
<rect x="{CANVAS_W - 142}" y="9" width="118" height="22" rx="4" fill="none" stroke="{t["border"]}"/>
<text x="{CANVAS_W - 83}" y="24" text-anchor="middle" font-family="{MONO}" font-size="12" fill="{t["text_dim"]}">portfolio ↗</text>'''

    # ---- sidebar ------------------------------------------------------- #
    sb_items = []
    row_y = TITLEBAR_H + 26 + 18
    sb_items.append(
        f'<text x="18" y="{TITLEBAR_H + 26}" font-family="{MONO}" font-size="10.5" letter-spacing="1" '
        f'fill="{t["text_faint"]}">~/ALEJANDRO-PEREZ</text>'
    )
    for glyph, label, active in SIDEBAR_TREE:
        color = t["gold"] if active else t["text_dim"]
        bar = f'<rect x="0" y="{row_y - 15}" width="2" height="22" fill="{t["gold"]}"/>' if active else ""
        fill = f'fill="{t["gold"]}" fill-opacity="0.06"' if active else ""
        if active:
            sb_items.append(f'<rect x="0" y="{row_y - 15}" width="{SIDEBAR_W}" height="22" {fill}/>')
        sb_items.append(bar)
        sb_items.append(
            f'<text x="18" y="{row_y}" font-family="{MONO}" font-size="13" fill="{t["text_faint"]}">{esc(glyph)}</text>'
            f'<text x="40" y="{row_y}" font-family="{MONO}" font-size="13" fill="{color}">{esc(label)}</text>'
        )
        row_y += 27
    row_y += 12
    sb_items.append(
        f'<text x="18" y="{row_y}" font-family="{MONO}" font-size="10.5" letter-spacing="1" '
        f'fill="{t["text_faint"]}">BUILD</text>'
    )
    row_y += 24
    glyph, label = BUILD_ITEM
    sb_items.append(
        f'<text x="18" y="{row_y}" font-family="{MONO}" font-size="13" fill="{t["text_faint"]}">{esc(glyph)}</text>'
        f'<text x="40" y="{row_y}" font-family="{MONO}" font-size="13" fill="{t["text_dim"]}">{esc(label)}</text>'
    )

    sidebar = f'''<rect x="0" y="{TITLEBAR_H}" width="{SIDEBAR_W}" height="{CANVAS_H - TITLEBAR_H - STATUSBAR_H}" fill="{t["sidebar"]}"/>
<path d="M{SIDEBAR_W} {TITLEBAR_H}V{CANVAS_H - STATUSBAR_H}" stroke="{t["border"]}"/>
{"".join(sb_items)}'''

    # ---- main: file tab + file body ------------------------------------ #
    tab_x = SIDEBAR_W + PAD
    tab_y = TITLEBAR_H + 18
    tab_w = 118
    body_x = SIDEBAR_W + PAD
    body_y = tab_y + 22
    body_w = CANVAS_W - body_x - PAD
    body_h = CANVAS_H - STATUSBAR_H - body_y - PAD

    file_tab = (
        f'<rect x="{tab_x}" y="{tab_y}" width="{tab_w}" height="22" rx="6" fill="{t["panel2"]}" stroke="{t["border"]}"/>'
        f'<text x="{tab_x + 12}" y="{tab_y + 15}" font-family="{MONO}" font-size="12" fill="{t["text_faint"]}">◆ whoami.md</text>'
    )

    file_body_bg = (
        f'<rect x="{body_x}" y="{body_y}" width="{body_w}" height="{body_h}" rx="8" fill="{t["panel"]}" stroke="{t["border"]}"/>'
    )

    av_x, av_y = body_x + 28, body_y + 28
    clip_id = f"avatar-clip-{theme_name}"
    avatar = (
        f'<defs><clipPath id="{clip_id}"><rect x="{av_x}" y="{av_y}" width="{AVATAR_SIZE}" height="{AVATAR_SIZE}" rx="12"/></clipPath></defs>'
        f'<image href="data:image/jpeg;base64,{avatar_b64}" x="{av_x}" y="{av_y}" width="{AVATAR_SIZE}" height="{AVATAR_SIZE}" '
        f'preserveAspectRatio="xMidYMid slice" clip-path="url(#{clip_id})"/>'
        f'<rect x="{av_x}" y="{av_y}" width="{AVATAR_SIZE}" height="{AVATAR_SIZE}" rx="12" fill="none" stroke="{t["border"]}"/>'
    )

    col_x = av_x + AVATAR_SIZE + 26
    col_w = body_x + body_w - PAD - col_x

    parts = []
    y = av_y + 14
    parts.append(
        f'<text x="{col_x}" y="{y}" font-family="{MONO}" font-size="13" fill="{t["text_faint"]}">'
        f'<tspan fill="{t["teal"]}">~$</tspan> whoami</text>'
    )
    y += 32
    parts.append(
        f'<text x="{col_x}" y="{y}" font-family="{MONO}" font-size="27" font-weight="700" fill="{t["text"]}">Alejandro Perez'
        f'<tspan fill="{t["gold"]}">'
        f'<animate attributeName="opacity" values="1;1;0;0;1" keyTimes="0;0.45;0.5;0.95;1" dur="1.1s" repeatCount="indefinite"/>'
        f" █</tspan></text>"
    )
    y += 30
    role_lines = wrap(ROLE_LINE, max(20, int(col_w / (15 * 0.605))))
    for line in role_lines:
        parts.append(
            f'<text x="{col_x}" y="{y}" font-family="{MONO}" font-size="15" font-weight="600" fill="{t["gold"]}">{esc(line)}</text>'
        )
        y += 21
    y += 6
    lede_lines = wrap(LEDE, max(20, int(col_w / (14 * 0.52))))[:2]
    for line in lede_lines:
        parts.append(
            f'<text x="{col_x}" y="{y}" font-family="{SANS}" font-size="14" fill="{t["text_dim"]}">{esc(line)}</text>'
        )
        y += 20
    y += 10
    badges_svg, y_after = badge_row(BADGES, col_x, y, col_w, t)
    parts.append(badges_svg)

    main = file_tab + file_body_bg + avatar + "".join(parts)

    # ---- status bar ----------------------------------------------------- #
    sy = CANVAS_H - STATUSBAR_H
    statusbar = f'''<rect x="0" y="{sy}" width="{CANVAS_W}" height="{STATUSBAR_H}" fill="{t["teal"]}"/>
<circle cx="18" cy="{sy + STATUSBAR_H / 2}" r="3.5" fill="{t["sidebar"] if theme_name == "dark" else "#06201d"}"/>
<text x="30" y="{sy + STATUSBAR_H / 2 + 4}" font-family="{MONO}" font-size="11.5" fill="{"#06201d" if theme_name == "light" else "#06201d"}">available — remote / hybrid</text>
<text x="270" y="{sy + STATUSBAR_H / 2 + 4}" font-family="{MONO}" font-size="11.5" fill="#06201d">Buenos Aires, AR</text>
<text x="440" y="{sy + STATUSBAR_H / 2 + 4}" font-family="{MONO}" font-size="11.5" fill="#06201d">UTF-8</text>
<text x="520" y="{sy + STATUSBAR_H / 2 + 4}" font-family="{MONO}" font-size="11.5" fill="#06201d">main</text>'''

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{CANVAS_W}" height="{CANVAS_H}" viewBox="0 0 {CANVAS_W} {CANVAS_H}" role="img" aria-labelledby="title desc">
<title id="title">Alejandro Perez — whoami.md</title>
<desc id="desc">GitHub profile hero styled like the alejandro-perez portfolio: file tree sidebar, whoami.md tab, prompt and skill badges.</desc>
<rect width="{CANVAS_W}" height="{CANVAS_H}" rx="14" fill="{t["bg"]}"/>
<clipPath id="frame-{theme_name}"><rect width="{CANVAS_W}" height="{CANVAS_H}" rx="14"/></clipPath>
<g clip-path="url(#frame-{theme_name})">
{titlebar}
{sidebar}
{main}
{statusbar}
</g>
<rect x="0.5" y="0.5" width="{CANVAS_W - 1}" height="{CANVAS_H - 1}" rx="14" fill="none" stroke="{t["border"]}"/>
</svg>'''


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--photo", required=True)
    parser.add_argument("--out-dark", required=True)
    parser.add_argument("--out-light", required=True)
    args = parser.parse_args()

    avatar_b64 = load_avatar_b64(args.photo)

    for theme_name, out_path in (("dark", args.out_dark), ("light", args.out_light)):
        svg = build_svg(theme_name, avatar_b64)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(svg)
        print(f"wrote {out_path} ({len(svg) / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
