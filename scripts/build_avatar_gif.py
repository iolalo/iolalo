#!/usr/bin/env python3
"""Build a looping 'particle assembly' GIF from a circular avatar PNG.

Splits the avatar into a tile grid, scatters the tiles off-canvas, then
animates them flying into place to form the photo, holds, and reverses.

Usage:
    python scripts/build_avatar_gif.py --avatar assets/avatar.png -o assets/avatar-assemble.gif
"""
import argparse
import math
import random

from PIL import Image

CANVAS = 480
BG = (13, 17, 23, 255)  # GitHub dark background #0d1117
AVATAR_SIZE = 420
GRID = 14
ASSEMBLE_FRAMES = 16
HOLD_FRAMES = 10
FRAME_DURATION_MS = 55


def ease_out_cubic(t):
    return 1 - (1 - t) ** 3


def ease_in_cubic(t):
    return t**3


def build_tiles(avatar_path, seed):
    random.seed(seed)
    margin = (CANVAS - AVATAR_SIZE) // 2
    tile_size = AVATAR_SIZE // GRID

    src = Image.open(avatar_path).convert("RGBA").resize((AVATAR_SIZE, AVATAR_SIZE), Image.LANCZOS)

    tiles = []
    for gy in range(GRID):
        for gx in range(GRID):
            box = (gx * tile_size, gy * tile_size, (gx + 1) * tile_size, (gy + 1) * tile_size)
            tile_img = src.crop(box)
            if tile_img.split()[3].getextrema()[1] == 0:
                continue  # fully transparent corner tile outside the circle, skip

            end_x = margin + box[0]
            end_y = margin + box[1]
            angle = random.uniform(0, 2 * math.pi)
            dist = random.uniform(CANVAS * 0.6, CANVAS * 1.3)
            tiles.append(
                {
                    "img": tile_img,
                    "start": (end_x + math.cos(angle) * dist, end_y + math.sin(angle) * dist),
                    "end": (end_x, end_y),
                    "rot": random.uniform(-120, 120),
                }
            )
    return tiles


def render_frame(tiles, progress, easing):
    canvas = Image.new("RGBA", (CANVAS, CANVAS), BG)
    e = easing(progress)
    for t in tiles:
        sx, sy = t["start"]
        ex, ey = t["end"]
        x = sx + (ex - sx) * e
        y = sy + (ey - sy) * e
        rot = t["rot"] * (1 - e)
        tile_img = t["img"]
        if abs(rot) > 0.5:
            tile_img = tile_img.rotate(rot, resample=Image.BICUBIC, expand=False)
        canvas.paste(tile_img, (int(x), int(y)), tile_img)
    return canvas.convert("RGB")


def build_frames(tiles):
    frames = []
    for i in range(ASSEMBLE_FRAMES + 1):
        frames.append(render_frame(tiles, i / ASSEMBLE_FRAMES, ease_out_cubic))

    final_frame = frames[-1]
    frames.extend([final_frame.copy() for _ in range(HOLD_FRAMES)])

    for i in range(1, ASSEMBLE_FRAMES + 1):
        frames.append(render_frame(tiles, 1 - (i / ASSEMBLE_FRAMES), ease_in_cubic))

    scattered = render_frame(tiles, 0, ease_out_cubic)
    frames.extend([scattered, scattered.copy()])
    return frames, final_frame


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--avatar", required=True, help="path to a circular RGBA avatar PNG")
    parser.add_argument("-o", "--output", required=True, help="output GIF path")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    tiles = build_tiles(args.avatar, args.seed)
    frames, final_frame = build_frames(tiles)

    palette_img = final_frame.convert("P", palette=Image.ADAPTIVE, colors=256)
    quantized = [f.quantize(palette=palette_img) for f in frames]

    quantized[0].save(
        args.output,
        save_all=True,
        append_images=quantized[1:],
        duration=FRAME_DURATION_MS,
        loop=0,
    )


if __name__ == "__main__":
    main()
