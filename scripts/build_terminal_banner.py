#!/usr/bin/env python3
"""Generate an animated 'profile.sh --live' terminal banner SVG (dark + light).

Dithers a photo to 1-bit, scatters the dark pixels into randomized clusters,
and animates each cluster with its own SMIL opacity dip + jitter -- so the
portrait continuously, unevenly reassembles and partially dissolves, forever,
with no JavaScript. Paired with a SYSTEM.INFO panel of real profile fields.

Usage:
    python scripts/build_terminal_banner.py --photo assets/avatar-square.png \
        --out-dark assets/banner-dark.svg --out-light assets/banner-light.svg
"""
import argparse
import random

import cv2
import numpy as np
from PIL import Image

CANVAS_W, CANVAS_H = 1000, 520
MAP_BOX = (30, 76, 460, 476)  # x0, y0, x1, y1
INFO_BOX = (490, 76, 970, 476)
DOT_TARGET = 6000
GROUP_SIZE_RANGE = (8, 20)
LOOP_MIN_DUR, LOOP_MAX_DUR = 9.0, 17.0

FIELDS = [
    ("Subject", "Alejandro"),
    ("Role", "BI Developer"),
    ("Origin", "Buenos Aires, AR"),
    ("Stack", "Power BI · DAX · Python"),
    ("Automation", "n8n"),
    ("Grid.Mail", "alejandro.fussion@gmail.com"),
    ("Grid.LinkedIn", "/in/alejandroperez-data"),
    ("Grid.GitHub", "iolalo"),
]

THEMES = {
    "dark": {
        "outer": "#0A101F",
        "panel": "#0D1628",
        "inner_panel": "#101B30",
        "border": "#25344C",
        "text_dim": "#8291A8",
        "text_bright": "#E7ECF3",
        "accent": "#38BDF8",
        "accent_dim_opacity": ".16",
    },
    "light": {
        "outer": "#F3F6FB",
        "panel": "#FFFFFF",
        "inner_panel": "#F8FAFD",
        "border": "#D7E0EC",
        "text_dim": "#5B6B84",
        "text_bright": "#0F1A2B",
        "accent": "#0284C7",
        "accent_dim_opacity": ".12",
    },
}

FONT = "ui-monospace,SFMono-Regular,Consolas,monospace"


def build_dots(photo_path, box, seed):
    x0, y0, x1, y1 = box
    pad = 12
    w, h = (x1 - x0 - 2 * pad), (y1 - y0 - 2 * pad)

    src = Image.open(photo_path).convert("RGBA")
    # crop to the box's aspect ratio before resizing, so the portrait isn't stretched
    src_w, src_h = src.size
    target_ratio = w / h
    src_ratio = src_w / src_h
    if src_ratio > target_ratio:
        new_w = int(src_h * target_ratio)
        left = (src_w - new_w) // 2
        src = src.crop((left, 0, left + new_w, src_h))
    else:
        new_h = int(src_w / target_ratio)
        top = (src_h - new_h) // 2
        src = src.crop((0, top, src_w, top + new_h))

    # flatten onto white first, so any transparent area (e.g. outside a circular
    # crop) contributes no dots instead of reading as black background
    flattened = Image.new("RGBA", src.size, (255, 255, 255, 255))
    flattened.alpha_composite(src)

    # CLAHE (local contrast) instead of a single global levels adjustment --
    # a photo lit unevenly (bright on one side, deep shadow on the other, e.g.
    # a single stage light) would otherwise dither to a blown-out blob on one
    # side and a solid shadow mass on the other, with no facial structure.
    gray_arr = np.array(flattened.convert("L"))
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    gray = Image.fromarray(clahe.apply(gray_arr))

    # Calibrate at a moderate resolution, then solve for the grid size that
    # lands close to DOT_TARGET dark pixels -- dithering directly at that
    # resolution (rather than dithering fine and randomly dropping dots) is
    # what keeps facial detail legible; random subsampling washes it out.
    calib_w = 150
    calib_h = max(1, int(calib_w * h / w))
    calib = gray.resize((calib_w, calib_h), Image.LANCZOS).convert("1", dither=Image.FLOYDSTEINBERG)
    calib_px = calib.load()
    dark_ratio = sum(1 for py in range(calib_h) for px in range(calib_w) if calib_px[px, py] == 0) / (
        calib_w * calib_h
    )
    dark_ratio = max(dark_ratio, 0.05)

    target_total = DOT_TARGET / dark_ratio
    grid_w = max(1, int((target_total * w / h) ** 0.5))
    grid_h = max(1, int(grid_w * h / w))

    gray = gray.resize((grid_w, grid_h), Image.LANCZOS)
    bitmap = gray.convert("1", dither=Image.FLOYDSTEINBERG)
    pixels = bitmap.load()

    raw_dots = [(px, py) for py in range(grid_h) for px in range(grid_w) if pixels[px, py] == 0]

    sx, sy = w / grid_w, h / grid_h
    dots = [(x0 + pad + px * sx, y0 + pad + py * sy) for px, py in raw_dots]
    # size each drawn dot to roughly fill its grid cell, so adjacent "on" cells
    # visually merge into dithered tone instead of reading as scattered specks
    dot_size = max(1, round((sx + sy) / 2 * 1.15))
    return dots, grid_w, grid_h, dot_size


def group_dots(dots, seed):
    rng = random.Random(seed + 1)
    rng.shuffle(dots)
    groups = []
    i = 0
    while i < len(dots):
        n = rng.randint(*GROUP_SIZE_RANGE)
        groups.append(dots[i : i + n])
        i += n
    return groups


def render_dot_groups(groups, accent, seed, dot_size):
    rng = random.Random(seed + 2)
    out = []
    for g in groups:
        d = "".join(f"M{x:.1f} {y:.1f}h{dot_size}" for x, y in g)
        dur = rng.uniform(LOOP_MIN_DUR, LOOP_MAX_DUR)
        begin = rng.uniform(0, dur)
        dip_start = rng.uniform(0.15, 0.45)
        dip_end = rng.uniform(dip_start + 0.15, 0.85)
        base_op = rng.uniform(0.75, 0.95)
        jx = rng.uniform(-6, 6)
        jy = rng.uniform(-6, 6)
        j_at = rng.uniform(0.3, 0.6)
        opacity_vals = f"{base_op:.2f};{base_op:.2f};0;0;0;0;{base_op:.2f}"
        opacity_times = f"0;{dip_start:.2f};{min(dip_start+0.06,0.99):.2f};{((dip_start+dip_end)/2):.2f};{max(dip_end-0.06,dip_start+0.01):.2f};{dip_end:.2f};1"
        translate_vals = f"0 0;0 0;{jx:.1f} {jy:.1f};0 0;0 0"
        translate_times = f"0;{max(j_at-0.08,0):.2f};{j_at:.2f};{min(j_at+0.08,1):.2f};1"
        out.append(
            f'<path d="{d}" fill="none" stroke="{accent}" stroke-width="{dot_size}" opacity="{base_op:.2f}">'
            f'<animate attributeName="opacity" begin="-{begin:.2f}s" dur="{dur:.2f}s" repeatCount="indefinite" '
            f'keyTimes="{opacity_times}" values="{opacity_vals}"/>'
            f'<animateTransform attributeName="transform" type="translate" begin="-{begin:.2f}s" dur="{dur:.2f}s" '
            f'repeatCount="indefinite" calcMode="linear" keyTimes="{translate_times}" values="{translate_vals}"/>'
            f"</path>"
        )
    return "".join(out)


def corner_brackets(box, accent):
    x0, y0, x1, y1 = box
    n = 12
    return (
        f'<path d="M{x0} {y0+n}h{n}M{x0} {y0+n}v-{n}'
        f"M{x1} {y0+n}h-{n}M{x1} {y0+n}v-{n}"
        f"M{x0} {y1-n}h{n}M{x0} {y1-n}v{n}"
        f'M{x1} {y1-n}h-{n}M{x1} {y1-n}v{n}" fill="none" stroke="{accent}" opacity=".55"/>'
    )


def build_svg(theme_name, dots, grid_w, grid_h, dot_size, seed):
    t = THEMES[theme_name]
    groups = group_dots(list(dots), seed)
    dot_markup = render_dot_groups(groups, t["accent"], seed, dot_size)

    mx0, my0, mx1, my1 = MAP_BOX
    ix0, iy0, ix1, iy1 = INFO_BOX

    fields_svg = []
    row_y = iy0 + 60
    for label, value in FIELDS:
        fields_svg.append(
            f'<text x="{ix0+18}" y="{row_y}" fill="{t["text_dim"]}" font-family="{FONT}" font-size="14">{label}</text>'
            f'<text x="{ix1-18}" y="{row_y}" text-anchor="end" fill="{t["accent"]}" font-family="{FONT}" '
            f'font-size="14" font-weight="600">{value}</text>'
        )
        row_y += 34

    status_y = iy1 - 24
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{CANVAS_W}" height="{CANVAS_H}" viewBox="0 0 {CANVAS_W} {CANVAS_H}" role="img" aria-labelledby="title desc">
<title id="title">Alejandro's live system profile</title>
<desc id="desc">Animated terminal banner with a dithered portrait that continuously reassembles.</desc>
<defs>
<clipPath id="mapClip-{theme_name}"><rect x="{mx0}" y="{my0}" width="{mx1-mx0}" height="{my1-my0}" rx="4"/></clipPath>
</defs>
<rect width="{CANVAS_W}" height="{CANVAS_H}" rx="18" fill="{t['outer']}"/>
<rect x="12" y="12" width="{CANVAS_W-24}" height="{CANVAS_H-24}" rx="13" fill="{t['panel']}" stroke="{t['border']}"/>
<path d="M12 54H{CANVAS_W-12}" stroke="{t['border']}"/>
<circle cx="36" cy="33" r="6" fill="#FF5F57"/>
<circle cx="57" cy="33" r="6" fill="#FEBC2E"/>
<circle cx="78" cy="33" r="6" fill="#28C840"/>
<text x="{CANVAS_W/2}" y="38" text-anchor="middle" fill="{t['text_dim']}" font-family="{FONT}" font-size="13" letter-spacing=".4">whoami --live</text>

<rect x="{mx0}" y="{my0}" width="{mx1-mx0}" height="{my1-my0}" rx="6" fill="{t['inner_panel']}" stroke="{t['border']}"/>
<path d="M{mx0} {my0+36}H{mx1}" stroke="{t['border']}"/>
<text x="{mx0+14}" y="{my0+24}" fill="{t['accent']}" font-family="{FONT}" font-size="13" font-weight="700" letter-spacing="1.2">VISUAL.MAP</text>
<text x="{mx1-14}" y="{my0+24}" text-anchor="end" fill="{t['text_dim']}" font-family="{FONT}" font-size="11">{grid_w}×{grid_h} / 1-BIT</text>
{corner_brackets((mx0+14, my0+52, mx1-14, my1-14), t['accent'])}
<g clip-path="url(#mapClip-{theme_name})" shape-rendering="crispEdges">
{dot_markup}
</g>

<rect x="{ix0}" y="{iy0}" width="{ix1-ix0}" height="{iy1-iy0}" rx="6" fill="{t['inner_panel']}" stroke="{t['border']}"/>
<path d="M{ix0} {iy0+36}H{ix1}" stroke="{t['border']}"/>
<text x="{ix0+14}" y="{iy0+24}" fill="{t['accent']}" font-family="{FONT}" font-size="13" font-weight="700" letter-spacing="1.2">SYSTEM.INFO</text>
<g filter="none"><circle cx="{ix1-166}" cy="{iy0+19}" r="4" fill="#22C55E"><animate attributeName="opacity" values="1;.3;1" dur="1.6s" repeatCount="indefinite"/></circle></g>
<text x="{ix1-156}" y="{iy0+24}" fill="#22C55E" font-family="{FONT}" font-size="12" font-weight="700">LIVE</text>
<rect x="{ix1-118}" y="{iy0+6}" width="118" height="20" rx="10" fill="{t['accent']}" opacity="{t['accent_dim_opacity']}" stroke="{t['accent']}"/>
<text x="{ix1-59}" y="{iy0+20}" text-anchor="middle" fill="{t['accent']}" font-family="{FONT}" font-size="11" font-weight="700">@iolalo</text>
{''.join(fields_svg)}
<path d="M{ix0} {status_y-16}H{ix1}" stroke="{t['border']}"/>
<circle cx="{ix0+16}" cy="{status_y}" r="3" fill="{t['accent']}"><animate attributeName="opacity" values="1;.25;1" dur="2.2s" repeatCount="indefinite"/></circle>
<text x="{ix0+28}" y="{status_y+4}" fill="{t['text_dim']}" font-family="{FONT}" font-size="11" letter-spacing=".4">STATUS: MODEL REFRESHED · 0 ERRORS</text>
</svg>'''
    return svg


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--photo", required=True)
    parser.add_argument("--out-dark", required=True)
    parser.add_argument("--out-light", required=True)
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()

    dots, grid_w, grid_h, dot_size = build_dots(args.photo, MAP_BOX, args.seed)

    for theme_name, out_path in (("dark", args.out_dark), ("light", args.out_light)):
        svg = build_svg(theme_name, dots, grid_w, grid_h, dot_size, args.seed)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(svg)
        print(f"wrote {out_path} ({len(svg)/1024:.0f} KB, {len(dots)} dots)")


if __name__ == "__main__":
    main()
