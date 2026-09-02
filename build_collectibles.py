from __future__ import annotations

import base64
import hashlib
import json
import math
import zipfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
FRAME_DIR = ROOT / "frames"
PREVIEW_DIR = ROOT / "previews"
SIZE = 16

# MakeCode Arcade's default 16-color palette. Index 0 is transparent.
PALETTE_HEX = [
    "#000000",
    "#ffffff",
    "#ff2121",
    "#ff93c4",
    "#ff8135",
    "#fff609",
    "#249ca3",
    "#78dc52",
    "#003fad",
    "#87f2ff",
    "#8e2ec4",
    "#a4839f",
    "#5c406c",
    "#e5cdc4",
    "#91463d",
    "#000000",
]
PALETTE_RGB = [tuple(int(value[i : i + 2], 16) for i in (1, 3, 5)) for value in PALETTE_HEX]


def blank() -> list[list[int]]:
    return [[0 for _ in range(SIZE)] for _ in range(SIZE)]


def clone(frame: list[list[int]]) -> list[list[int]]:
    return [row[:] for row in frame]


def pixel(frame: list[list[int]], x: int, y: int, color: int) -> None:
    if 0 <= x < SIZE and 0 <= y < SIZE:
        frame[y][x] = color


def rect(frame: list[list[int]], x0: int, y0: int, x1: int, y1: int, color: int) -> None:
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            pixel(frame, x, y, color)


def line(frame: list[list[int]], x0: int, y0: int, x1: int, y1: int, color: int) -> None:
    dx = abs(x1 - x0)
    sx = 1 if x0 < x1 else -1
    dy = -abs(y1 - y0)
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    while True:
        pixel(frame, x0, y0, color)
        if x0 == x1 and y0 == y1:
            return
        twice = 2 * err
        if twice >= dy:
            err += dy
            x0 += sx
        if twice <= dx:
            err += dx
            y0 += sy


def shift(frame: list[list[int]], dx: int = 0, dy: int = 0) -> list[list[int]]:
    moved = blank()
    for y, row in enumerate(frame):
        for x, color in enumerate(row):
            if color:
                pixel(moved, x + dx, y + dy, color)
    return moved


def mirror(frame: list[list[int]]) -> list[list[int]]:
    return [list(reversed(row)) for row in frame]


def mask_ellipse(cx: float, cy: float, rx: float, ry: float) -> set[tuple[int, int]]:
    return {
        (x, y)
        for y in range(SIZE)
        for x in range(SIZE)
        if ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1
    }


def mask_polygon(points: list[tuple[float, float]]) -> set[tuple[int, int]]:
    result: set[tuple[int, int]] = set()
    for y in range(SIZE):
        py = y + 0.5
        for x in range(SIZE):
            px = x + 0.5
            inside = False
            j = len(points) - 1
            for i, (xi, yi) in enumerate(points):
                xj, yj = points[j]
                if (yi > py) != (yj > py):
                    cross = (xj - xi) * (py - yi) / (yj - yi) + xi
                    if px < cross:
                        inside = not inside
                j = i
            if inside:
                result.add((x, y))
    return result


def paint_mask(frame: list[list[int]], mask: set[tuple[int, int]], outline: int, fill: int) -> None:
    for x, y in mask:
        edge = any((x + dx, y + dy) not in mask for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        frame[y][x] = outline if edge else fill


def sparkle(frame: list[list[int]], x: int, y: int, color: int = 1, radius: int = 1) -> None:
    pixel(frame, x, y, color)
    for distance in range(1, radius + 1):
        pixel(frame, x - distance, y, color)
        pixel(frame, x + distance, y, color)
        pixel(frame, x, y - distance, color)
        pixel(frame, x, y + distance, color)


def image_from_frame(frame: list[list[int]]) -> Image.Image:
    image = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    for y, row in enumerate(frame):
        for x, index in enumerate(row):
            if index:
                image.putpixel((x, y), (*PALETTE_RGB[index], 255))
    return image


def encode_f4(frame: list[list[int]]) -> bytes:
    result = bytearray([0x87, 0x04, SIZE, 0, SIZE, 0, 0, 0])
    for x in range(SIZE):
        for y in range(0, SIZE, 2):
            result.append(frame[y][x] | (frame[y + 1][x] << 4))
    return bytes(result)


def ascii_rows(frame: list[list[int]]) -> list[str]:
    return ["".join("." if value == 0 else format(value, "x") for value in row) for row in frame]


def draw_coin(width: int, highlight_right: bool = False) -> list[list[int]]:
    frame = blank()
    mask = mask_ellipse(7.5, 7.5, max(0.8, width / 2), 6)
    paint_mask(frame, mask, 14, 5)
    for x, y in mask:
        if frame[y][x] == 5 and ((x >= 8) if highlight_right else (x <= 6)):
            frame[y][x] = 4
    if width >= 8:
        rect(frame, 7, 5, 8, 10, 14)
        pixel(frame, 6 if not highlight_right else 9, 4, 1)
        pixel(frame, 6 if not highlight_right else 9, 5, 1)
    elif width >= 5:
        line(frame, 7, 4, 7, 11, 5)
        pixel(frame, 7 if not highlight_right else 8, 4, 1)
    else:
        line(frame, 8, 3, 8, 12, 5)
        pixel(frame, 8, 4, 1)
    return frame


def draw_orb(dy: int, phase: int) -> list[list[int]]:
    frame = blank()
    mask = mask_ellipse(7.5, 7.5 + dy, 5, 5)
    paint_mask(frame, mask, 8, 6)
    for x, y in mask:
        if frame[y][x] == 6 and x + y < 13 + dy:
            frame[y][x] = 9
    sparkle(frame, 6 + (phase % 2), 5 + dy + (phase // 2), 1)
    aura = [((1, 7), (14, 8)), ((3, 2), (12, 13)), ((1, 9), (14, 6)), ((4, 14), (11, 1))][phase]
    for x, y in aura:
        pixel(frame, x, y + dy, 9)
    return frame


def draw_gem(dy: int, phase: int) -> list[list[int]]:
    frame = blank()
    points = [(7.5, 1.5 + dy), (13.5, 6 + dy), (7.5, 14 + dy), (1.5, 6 + dy)]
    mask = mask_polygon(points)
    paint_mask(frame, mask, 8, 9)
    line(frame, 3, 6 + dy, 7, 12 + dy, 6)
    line(frame, 12, 6 + dy, 8, 12 + dy, 6)
    line(frame, 4, 5 + dy, 11, 5 + dy, 1)
    pixel(frame, 4 + phase * 2, 4 + dy + (phase % 2), 1)
    if phase in (1, 3):
        pixel(frame, 14 if phase == 1 else 1, 3 + dy, 9)
    return frame


STAR_POINTS = [(7.5, 0.5), (9.5, 5), (14.5, 5.5), (10.5, 9), (12, 14), (7.5, 11), (3, 14), (4.5, 9), (0.5, 5.5), (5.5, 5)]


def draw_star(phase: int) -> list[list[int]]:
    frame = blank()
    scale = 0.88 if phase == 3 else 1.0
    points = [(7.5 + (x - 7.5) * scale, 7.5 + (y - 7.5) * scale) for x, y in STAR_POINTS]
    mask = mask_polygon(points)
    paint_mask(frame, mask, 4, 5)
    pixel(frame, 6, 5, 1)
    pixel(frame, 7, 4, 1)
    if phase == 1:
        sparkle(frame, 14, 2, 1)
    elif phase == 2:
        sparkle(frame, 1, 12, 5)
    elif phase == 3:
        pixel(frame, 13, 11, 5)
    return frame


def heart_mask(scale: float, dy: int) -> set[tuple[int, int]]:
    base = mask_polygon([(2, 4), (4, 2), (7.5, 4), (11, 2), (14, 4), (13, 9), (7.5, 14), (2, 9)])
    transformed: set[tuple[int, int]] = set()
    for x, y in base:
        nx = round(7.5 + (x - 7.5) * scale)
        ny = round(8 + (y - 8) * scale) + dy
        if 0 <= nx < SIZE and 0 <= ny < SIZE:
            transformed.add((nx, ny))
    return transformed


def draw_heart(scale: float, dy: int, phase: int) -> list[list[int]]:
    frame = blank()
    mask = heart_mask(scale, dy)
    paint_mask(frame, mask, 14, 2)
    for x, y in mask:
        if frame[y][x] == 2 and x <= 6 and y <= 7 + dy:
            frame[y][x] = 3
    pixel(frame, 5, 4 + dy, 1)
    if phase == 1:
        pixel(frame, 1, 5, 3)
        pixel(frame, 14, 5, 3)
    return frame


def draw_key(dy: int, phase: int) -> list[list[int]]:
    frame = blank()
    outer = mask_ellipse(4.5, 6.5 + dy, 3.5, 3.5)
    paint_mask(frame, outer, 14, 5)
    inner = mask_ellipse(4.5, 6.5 + dy, 1.2, 1.2)
    for x, y in inner:
        frame[y][x] = 0
    rect(frame, 7, 6 + dy, 13, 8 + dy, 14)
    rect(frame, 8, 6 + dy, 12, 6 + dy, 5)
    rect(frame, 11, 9 + dy, 13, 10 + dy, 14)
    rect(frame, 9, 8 + dy, 10, 9 + dy, 14)
    pixel(frame, 8 + phase, 5 + dy, 1)
    if phase == 2:
        sparkle(frame, 13, 3 + dy, 5)
    return frame


def draw_potion(dy: int, phase: int) -> list[list[int]]:
    frame = blank()
    rect(frame, 6, 1 + dy, 9, 3 + dy, 14)
    rect(frame, 7, 1 + dy, 8, 2 + dy, 13)
    rect(frame, 5, 3 + dy, 10, 4 + dy, 8)
    body = mask_polygon([(5, 4 + dy), (10, 4 + dy), (13, 12 + dy), (11, 14 + dy), (4, 14 + dy), (2, 12 + dy)])
    paint_mask(frame, body, 8, 9)
    for y in range(9 + dy, 14 + dy):
        for x in range(2, 14):
            if (x, y) in body and frame[y][x] != 8:
                frame[y][x] = 10
    line(frame, 3, 9 + dy, 12, 9 + dy, 3)
    pixel(frame, 4, 6 + dy, 1)
    bubble_positions = [(10, 11), (7, 10), (9, 7), (6, 6)]
    bx, by = bubble_positions[phase]
    pixel(frame, bx, by + dy, 3)
    if phase == 3:
        pixel(frame, 11, 3 + dy, 10)
    return frame


def draw_berries(dy: int, phase: int) -> list[list[int]]:
    frame = blank()
    left = mask_ellipse(5, 9 + dy, 3.5, 3.5)
    right = mask_ellipse(10, 9 + dy, 3.5, 3.5)
    paint_mask(frame, left, 14, 2)
    paint_mask(frame, right, 14, 2)
    pixel(frame, 4, 7 + dy, 3)
    pixel(frame, 9, 7 + dy, 3)
    line(frame, 5, 6 + dy, 7, 2 + dy, 7)
    line(frame, 10, 6 + dy, 7, 2 + dy, 7)
    leaf_x = 8 if phase in (0, 3) else 9
    rect(frame, leaf_x, 2 + dy, leaf_x + 2, 3 + dy, 7)
    pixel(frame, 3, 8 + dy, 1)
    return frame


def draw_gear(phase: int) -> list[list[int]]:
    frame = blank()
    center = mask_ellipse(7.5, 7.5, 5, 5)
    paint_mask(frame, center, 12, 11)
    cardinal = [(7, 1), (8, 1), (7, 14), (8, 14), (1, 7), (1, 8), (14, 7), (14, 8)]
    diagonal = [(3, 3), (12, 3), (3, 12), (12, 12), (4, 2), (11, 2), (2, 11), (13, 11)]
    teeth = cardinal if phase % 2 == 0 else diagonal
    for x, y in teeth:
        pixel(frame, x, y, 12)
        pixel(frame, x + (1 if x < 8 else -1), y + (1 if y < 8 else -1), 11)
    hole = mask_ellipse(7.5, 7.5, 2, 2)
    for x, y in hole:
        frame[y][x] = 0 if 6 <= x <= 9 and 6 <= y <= 9 else 12
    shine = [(5, 4), (10, 4), (10, 11), (5, 11)][phase]
    pixel(frame, shine[0], shine[1], 1)
    return frame


def draw_battery(dy: int, phase: int) -> list[list[int]]:
    frame = blank()
    rect(frame, 6, 1 + dy, 9, 2 + dy, 11)
    rect(frame, 4, 2 + dy, 11, 14 + dy, 8)
    rect(frame, 5, 3 + dy, 10, 13 + dy, 12)
    charge = [3, 6, 9, 6][phase]
    rect(frame, 6, 12 + dy - charge, 9, 12 + dy, 6)
    if phase in (1, 2):
        rect(frame, 7, 11 + dy - charge, 8, 12 + dy - charge, 9)
    pixel(frame, 5, 3 + dy, 1)
    if phase == 2:
        pixel(frame, 2, 7 + dy, 9)
        pixel(frame, 13, 7 + dy, 9)
    return frame


def draw_crown(dy: int, phase: int) -> list[list[int]]:
    frame = blank()
    points = [(2, 4 + dy), (5, 7 + dy), (7.5, 2 + dy), (10, 7 + dy), (13, 4 + dy), (12, 12 + dy), (3, 12 + dy)]
    mask = mask_polygon(points)
    paint_mask(frame, mask, 14, 5)
    rect(frame, 3, 10 + dy, 12, 12 + dy, 14)
    rect(frame, 4, 10 + dy, 11, 10 + dy, 5)
    pixel(frame, 7, 9 + dy, 10)
    pixel(frame, 8, 9 + dy, 10)
    pixel(frame, 4, 5 + dy, 1)
    if phase == 1:
        sparkle(frame, 14, 2 + dy, 1)
    elif phase == 3:
        pixel(frame, 1, 3 + dy, 5)
    return frame


def draw_feather(dx: int, dy: int, phase: int) -> list[list[int]]:
    frame = blank()
    # Dark quill and two offset vanes make this read as a feather, not a shard.
    line(frame, 4 + dx, 13 + dy, 11 + dx, 3 + dy, 8)
    line(frame, 5 + dx, 13 + dy, 11 + dx, 4 + dy, 13)
    vane = [(10, 3), (12, 3), (12, 5), (10, 6), (12, 6), (10, 8), (8, 9), (8, 5), (6, 7), (7, 10), (5, 10)]
    for x, y in vane:
        pixel(frame, x + dx, y + dy, 9 if (x + y + phase) % 3 else 1)
    pixel(frame, 4 + dx, 14 + dy, 11)
    motes = [(2, 4), (13, 9), (2, 11), (13, 2)]
    mx, my = motes[phase]
    pixel(frame, mx, my, 9)
    return frame


def ring(frame: list[list[int]], radius: int, color: int, phase: int = 0) -> None:
    cx = cy = 7.5
    for y in range(SIZE):
        for x in range(SIZE):
            distance = math.hypot(x - cx, y - cy)
            if abs(distance - radius) < 0.55 and (x + y + phase) % 2 == 0:
                pixel(frame, x, y, color)


STYLE_PARTICLES: dict[str, tuple[list[tuple[int, int]], list[tuple[int, int]]]] = {
    "coin": ([(7, 1), (14, 7), (8, 14), (1, 8)], [(2, 2), (13, 3), (12, 13), (3, 12)]),
    "orb": ([(7, 2), (12, 4), (13, 10), (8, 13), (3, 11), (2, 5)], [(7, 0), (15, 8), (7, 15), (0, 7)]),
    "gem": ([(3, 3), (12, 3), (12, 12), (3, 12)], [(1, 1), (14, 2), (13, 14), (2, 13)]),
    "star": ([(7, 1), (14, 7), (8, 14), (1, 8)], [(3, 2), (13, 4), (11, 13), (2, 11)]),
    "heart": ([(4, 4), (11, 4), (4, 11), (11, 11)], [(2, 3), (13, 3), (10, 14), (5, 14)]),
    "key": ([(2, 7), (6, 2), (12, 4), (13, 10), (8, 13)], [(1, 12), (5, 1), (14, 5), (12, 14)]),
    "potion": ([(5, 11), (9, 9), (7, 5), (11, 3)], [(3, 12), (7, 8), (10, 5), (13, 1)]),
    "berries": ([(3, 6), (12, 6), (5, 12), (10, 12)], [(1, 4), (14, 5), (12, 14), (3, 13)]),
    "gear": ([(2, 7), (4, 3), (8, 2), (12, 4), (13, 8), (11, 12), (7, 13), (3, 11)], [(1, 1), (14, 2), (13, 14), (2, 13)]),
    "battery": ([(3, 9), (5, 6), (7, 8), (9, 5), (12, 7)], [(1, 11), (4, 2), (11, 13), (14, 4)]),
    "crown": ([(3, 5), (7, 2), (12, 5), (5, 11), (10, 11)], [(1, 2), (14, 2), (13, 13), (2, 13)]),
    "feather": ([(4, 11), (6, 8), (8, 6), (10, 3)], [(2, 13), (5, 9), (9, 5), (13, 1)]),
}


def collected_frames(base: list[list[int]], main: int, light: int, dark: int, style: str) -> list[list[list[int]]]:
    flash = blank()
    for y, row in enumerate(base):
        for x, value in enumerate(row):
            if value:
                flash[y][x] = 1 if (x + y) % 3 else light
    sparkle(flash, 7, 7, 1, 2)

    pop = blank()
    ring(pop, 4, main)
    sparkle(pop, 7, 7, 1, 2)
    inner, outer = STYLE_PARTICLES[style]
    for index, (x, y) in enumerate(inner):
        pixel(pop, x, y, light if index % 2 else main)
    if style == "heart":
        pixel(pop, 4, 5, 3)
        pixel(pop, 11, 5, 3)
    elif style == "battery":
        line(pop, 4, 10, 6, 7, 9)
        line(pop, 9, 8, 11, 5, 9)
    elif style == "potion":
        pixel(pop, 6, 4, 3)
        pixel(pop, 10, 2, 10)

    burst = blank()
    ring(burst, 7, dark, 1)
    for index, (x, y) in enumerate(outer):
        pixel(burst, x, y, 1 if index == 0 else main)
        if style in {"gem", "gear", "star", "crown"}:
            pixel(burst, x + (1 if x < 8 else -1), y, light)
    if style == "feather":
        line(burst, 4, 12, 9, 4, light)
    elif style == "coin":
        for x, y in ((7, 1), (14, 7), (8, 14), (1, 8)):
            sparkle(burst, x, y, main)

    fade = blank()
    for index, (x, y) in enumerate(outer):
        if index % 2 == 0 or style in {"orb", "gear"}:
            pixel(fade, x, y, main if index else light)
    return [flash, pop, burst, fade]


def build_families() -> list[dict]:
    families = [
        {"id": "coin", "name": "Spinning Coin", "idle_ms": 120, "colors": (5, 1, 4), "idle": [draw_coin(10), draw_coin(6), draw_coin(2), draw_coin(6, True)]},
        {"id": "orb", "name": "Bobbing Energy Orb", "idle_ms": 150, "colors": (9, 1, 8), "idle": [draw_orb(dy, phase) for phase, dy in enumerate((0, -1, 0, 1))]},
        {"id": "gem", "name": "Shimmering Crystal", "idle_ms": 140, "colors": (9, 1, 6), "idle": [draw_gem(dy, phase) for phase, dy in enumerate((0, -1, 0, 1))]},
        {"id": "star", "name": "Pulsing Star", "idle_ms": 130, "colors": (5, 1, 4), "idle": [draw_star(phase) for phase in range(4)]},
        {"id": "heart", "name": "Beating Heart", "idle_ms": 150, "colors": (2, 1, 3), "idle": [draw_heart(scale, dy, phase) for phase, (scale, dy) in enumerate(((1.0, 0), (1.08, -1), (1.0, 0), (0.92, 1)))]},
        {"id": "key", "name": "Glinting Key", "idle_ms": 150, "colors": (5, 1, 14), "idle": [draw_key(dy, phase) for phase, dy in enumerate((0, -1, 0, 1))]},
        {"id": "potion", "name": "Bubbling Potion", "idle_ms": 160, "colors": (10, 3, 8), "idle": [draw_potion(dy, phase) for phase, dy in enumerate((0, 0, -1, 0))]},
        {"id": "berries", "name": "Bouncing Berries", "idle_ms": 150, "colors": (2, 3, 7), "idle": [draw_berries(dy, phase) for phase, dy in enumerate((0, -1, 0, 1))]},
        {"id": "gear", "name": "Turning Gear", "idle_ms": 120, "colors": (11, 1, 12), "idle": [draw_gear(phase) for phase in range(4)]},
        {"id": "battery", "name": "Pulsing Energy Cell", "idle_ms": 140, "colors": (9, 1, 8), "idle": [draw_battery(dy, phase) for phase, dy in enumerate((0, 0, -1, 0))]},
        {"id": "crown", "name": "Floating Crown", "idle_ms": 150, "colors": (5, 1, 14), "idle": [draw_crown(dy, phase) for phase, dy in enumerate((0, -1, 0, 1))]},
        {"id": "feather", "name": "Drifting Feather", "idle_ms": 170, "colors": (9, 1, 8), "idle": [draw_feather(dx, dy, phase) for phase, (dx, dy) in enumerate(((0, 0), (1, -1), (0, 0), (-1, 1)))]},
    ]
    for family in families:
        main, light, dark = family["colors"]
        family["collected"] = collected_frames(family["idle"][0], main, light, dark, family["id"])
        family["collected_ms"] = 75
    return families


def font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    candidates = ["arialbd.ttf" if bold else "arial.ttf", "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            pass
    return ImageFont.load_default()


def checker(size: int) -> Image.Image:
    image = Image.new("RGB", (size, size), "#332a3e")
    draw = ImageDraw.Draw(image)
    block = max(4, size // 8)
    for y in range(0, size, block):
        for x in range(0, size, block):
            if (x // block + y // block) % 2:
                draw.rectangle((x, y, x + block - 1, y + block - 1), fill="#463951")
    return image


def sprite_panel(frame: list[list[int]], scale: int = 5) -> Image.Image:
    size = SIZE * scale
    panel = checker(size)
    sprite = image_from_frame(frame).resize((size, size), Image.Resampling.NEAREST)
    panel.paste(sprite, (0, 0), sprite)
    return panel


def make_contact_sheet(families: list[dict]) -> None:
    left = 190
    scale = 4
    frame_size = SIZE * scale
    gap = 8
    row_height = 100
    width = left + 8 * (frame_size + gap) + 24
    height = 70 + len(families) * row_height
    image = Image.new("RGB", (width, height), "#171320")
    draw = ImageDraw.Draw(image)
    title_font = font(24, True)
    body_font = font(15, True)
    small_font = font(12)
    draw.text((20, 14), "Animated Platformer Collectibles", fill="#fff1e8", font=title_font)
    draw.text((left, 48), "IDLE — 4 FRAME LOOP", fill="#87f2ff", font=small_font)
    draw.text((left + 4 * (frame_size + gap), 48), "COLLECTED — 4 FRAME ONE-SHOT", fill="#ff93c4", font=small_font)
    for row_index, family in enumerate(families):
        top = 68 + row_index * row_height
        draw.rounded_rectangle((10, top, width - 10, top + 91), 8, fill="#241c2e", outline="#5c406c")
        draw.text((22, top + 22), family["name"], fill="#fff1e8", font=body_font)
        draw.text((22, top + 49), f"{family['idle_ms']} ms / {family['collected_ms']} ms", fill="#a4839f", font=small_font)
        for index, frame in enumerate(family["idle"] + family["collected"]):
            x = left + index * (frame_size + gap)
            image.paste(sprite_panel(frame, scale), (x, top + 12))
    image.save(ROOT / "contact-sheet.png")


def make_animated_previews(families: list[dict]) -> None:
    PREVIEW_DIR.mkdir(exist_ok=True)
    timeline: list[tuple[str, int, int]] = []
    for _ in range(2):
        timeline.extend(("idle", index, 135) for index in range(4))
    timeline.extend(("collected", index, 80) for index in range(4))
    timeline.extend([("collected", 3, 200), ("idle", 0, 250)])

    grid_frames: list[Image.Image] = []
    durations: list[int] = []
    columns = 4
    cell_width = 210
    cell_height = 165
    for animation_name, frame_index, duration in timeline:
        canvas = Image.new("RGB", (columns * cell_width, 3 * cell_height), "#171320")
        draw = ImageDraw.Draw(canvas)
        for family_index, family in enumerate(families):
            row, col = divmod(family_index, columns)
            left = col * cell_width
            top = row * cell_height
            draw.rounded_rectangle((left + 7, top + 7, left + cell_width - 7, top + cell_height - 7), 10, fill="#2b2238", outline="#5c406c", width=2)
            selected = family[animation_name][frame_index]
            panel = sprite_panel(selected, 7)
            canvas.paste(panel, (left + 49, top + 16))
            label = family["name"]
            label_font = font(14, True)
            bounds = draw.textbbox((0, 0), label, font=label_font)
            draw.text((left + (cell_width - (bounds[2] - bounds[0])) / 2, top + 136), label, fill="#fff1e8", font=label_font)
            state = "IDLE" if animation_name == "idle" else "COLLECTED"
            draw.text((left + 12, top + 12), state, fill="#87f2ff" if state == "IDLE" else "#ff93c4", font=font(10, True))
        grid_frames.append(canvas)
        durations.append(duration)
    grid_frames[0].save(ROOT / "collectibles-preview.gif", save_all=True, append_images=grid_frames[1:], duration=durations, loop=0, disposal=2, optimize=False)

    for family in families:
        frames: list[Image.Image] = []
        item_durations: list[int] = []
        for animation_name, frame_index, duration in timeline:
            canvas = Image.new("RGB", (192, 224), "#171320")
            draw = ImageDraw.Draw(canvas)
            panel = sprite_panel(family[animation_name][frame_index], 10)
            canvas.paste(panel, (16, 16))
            draw.text((16, 184), family["name"], fill="#fff1e8", font=font(15, True))
            state = "idle loop" if animation_name == "idle" else "collected one-shot"
            draw.text((16, 204), state, fill="#87f2ff" if animation_name == "idle" else "#ff93c4", font=font(11))
            frames.append(canvas)
            item_durations.append(duration)
        frames[0].save(PREVIEW_DIR / f"{family['id']}.gif", save_all=True, append_images=frames[1:], duration=item_durations, loop=0, disposal=2, optimize=False)


def ts_image(frame: list[list[int]]) -> str:
    rows = [" ".join("." if value == 0 else format(value, "x") for value in row) for row in frame]
    return "img`\n" + "\n".join(rows) + "\n`"


def write_project_files(families: list[dict]) -> None:
    jres: dict[str, object] = {"*": {"mimeType": "image/x-mkcd-f4", "dataEncoding": "base64", "namespace": "collectibles"}}
    animations: list[dict] = []
    for family in families:
        for state in ("idle", "collected"):
            animation_id = f"{family['id']}{state.title()}"
            frame_ids: list[str] = []
            for index, frame in enumerate(family[state], start=1):
                frame_id = f"{animation_id}{index}"
                frame_ids.append(f"collectibles.{frame_id}")
                jres[frame_id] = {"data": base64.b64encode(encode_f4(frame)).decode("ascii"), "mimeType": "image/x-mkcd-f4"}
            display_name = f"{family['name']} - {'Idle' if state == 'idle' else 'Collected'}"
            jres[animation_id] = {
                "namespace": "collectibles",
                "id": animation_id,
                "mimeType": "application/mkcd-animation",
                "dataEncoding": "json",
                "data": json.dumps({"frames": frame_ids, "flippedHorizontal": False}, separators=(",", ":")),
                "displayName": display_name,
            }
            animations.append({"id": animation_id, "display_name": display_name, "frames": family[state]})
    (ROOT / "images.g.jres").write_text(json.dumps(jres, indent=4) + "\n", encoding="utf-8")

    lines = ["// Auto-generated code. Do not edit.", "namespace collectibles {", "    helpers._registerFactory(\"animation\", function(name: string) {", "        switch (helpers.stringTrim(name)) {"]
    for animation in animations:
        lines.extend([f"            case \"{animation['display_name']}\":", f"            case \"{animation['id']}\": return ["])
        for frame in animation["frames"]:
            literal = ts_image(frame).replace("\n", "\n                ")
            lines.append(f"                {literal},")
        lines.append("            ];")
    lines.extend(["        }", "        return null;", "    })", "}", "// Auto-generated code. Do not edit.", ""])
    (ROOT / "images.g.ts").write_text("\n".join(lines), encoding="utf-8")
    (ROOT / "assets.json").write_text("", encoding="utf-8")
    (ROOT / "main.ts").write_text("", encoding="utf-8")
    (ROOT / "main.blocks").write_text('<xml xmlns="https://developers.google.com/blockly/xml"></xml>\n', encoding="utf-8")
    (ROOT / "tsconfig.json").write_text(json.dumps({"compilerOptions": {"target": "ES5", "noImplicitAny": True, "outDir": "built", "rootDir": "."}, "exclude": ["pxt_modules/**/*test.ts"]}, indent=4) + "\n", encoding="utf-8")
    (ROOT / ".gitignore").write_text("built/\npxt_modules/\n*.uf2\n*.hex\n", encoding="utf-8")

    test_lines = ["// Compile-only asset resolution test. This file is not imported with the asset pack.", "const collectibleAnimationSmokeTest: Image[][] = ["]
    for animation in animations:
        test_lines.append(f"    assets.animation`{animation['display_name']}`,")
    test_lines.extend(["];", "", "if (collectibleAnimationSmokeTest.length != 24) {", "    control.panic(24)", "}", ""])
    (ROOT / "test.ts").write_text("\n".join(test_lines), encoding="utf-8")

    config = {
        "name": "Platformer Animated Collectibles",
        "version": "0.0.1",
        "description": "Twelve original 16x16 collectibles with compact idle loops and custom collected animations for MakeCode Arcade.",
        "files": ["main.blocks", "main.ts", "README.md", "assets.json", "images.g.jres", "images.g.ts"],
        "preferredEditor": "blocksprj",
        "supportedTargets": ["arcade"],
        "dependencies": {"device": "*"},
        "testDependencies": {},
        "testFiles": ["test.ts"],
        "assetPack": True,
    }
    (ROOT / "pxt.json").write_text(json.dumps(config, indent=4) + "\n", encoding="utf-8")

    readme = """# Platformer Animated Collectibles

An original MakeCode Arcade asset pack with **12 collectible families**, each containing:

- a compact **4-frame idle loop**;
- a custom **4-frame collected one-shot**; and
- exact 16×16 artwork using Arcade's default palette.

![Animated preview](collectibles-preview.gif)

Included collectibles: spinning coin, energy orb, crystal, star, heart, key, potion, berries, gear, energy cell, crown, and feather.

## Use in MakeCode Arcade

After this folder is published as a public GitHub repository, add its GitHub URL through **Settings → Extensions**. Because `assetPack` is enabled, the named animations appear in the Animation gallery and the pack's code is ignored.

For each item, choose the matching `Idle` and `Collected` animations. Loop the idle animation. Run the collected animation once, then destroy or hide the collectible after the final frame. The custom collection sequences already supply the flash, ring, shards, sparks, bubbles, or trailing motes, so no stock destroyed effect is needed.

Suggested timing is recorded in `animation-manifest.json`. Idle loops use 120–170 ms per frame; collected animations use 75 ms per frame and should not loop.

## Contents

- `images.g.jres` / `images.g.ts`: MakeCode animation assets
- `test.ts`: compile-only resolution check for all 24 named animations
- `contact-sheet.png`: every exact frame at readable scale
- `collectibles-preview.gif`: combined animated preview
- `previews/`: one animated preview per collectible
- `frames/`: every source frame as a lossless PNG
- `ANIMATION_ASCII.md`: exact palette-index pixels
- `animation-manifest.json`: dimensions, timing, hashes, and validation facts
- `build_collectibles.py`: deterministic source generator

## License

MIT. These assets may be used, changed, and redistributed in student projects and tutorials under the terms in `LICENSE`.
"""
    (ROOT / "README.md").write_text(readme, encoding="utf-8")

    license_text = """MIT License

Copyright (c) 2026 Platformer Animated Collectibles contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
    (ROOT / "LICENSE").write_text(license_text, encoding="utf-8")


def write_frames_and_manifest(families: list[dict]) -> None:
    FRAME_DIR.mkdir(exist_ok=True)
    ascii_doc = ["# Exact 16×16 animation pixels", "", "`.` is transparency; `1`–`f` are MakeCode Arcade palette indices.", ""]
    manifest_families = []
    for family in families:
        item_dir = FRAME_DIR / family["id"]
        item_dir.mkdir(exist_ok=True)
        states = {}
        for state in ("idle", "collected"):
            frame_entries = []
            ascii_doc.extend([f"## {family['name']} — {state.title()}", ""])
            for index, frame in enumerate(family[state], start=1):
                name = f"{state}-{index}.png"
                path = item_dir / name
                image_from_frame(frame).save(path)
                f4 = encode_f4(frame)
                frame_entries.append({
                    "index": index,
                    "png": str(path.relative_to(ROOT)).replace("\\", "/"),
                    "png_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                    "f4_sha256": hashlib.sha256(f4).hexdigest(),
                    "opaque_pixels": sum(value != 0 for row in frame for value in row),
                })
                ascii_doc.extend([f"### Frame {index}", "", "```text", *ascii_rows(frame), "```", ""])
            states[state] = {
                "animation_id": f"{family['id']}{state.title()}",
                "frame_ms": family[f"{state}_ms"],
                "loop": state == "idle",
                "frames": frame_entries,
            }
        manifest_families.append({"id": family["id"], "name": family["name"], "width": SIZE, "height": SIZE, "states": states})
    (ROOT / "ANIMATION_ASCII.md").write_text("\n".join(ascii_doc), encoding="utf-8")

    all_animations = [entry for family in manifest_families for entry in family["states"].values()]
    manifest = {
        "pack": "Platformer Animated Collectibles",
        "version": "0.0.1",
        "generator": "build_collectibles.py",
        "license": "MIT",
        "palette": PALETTE_HEX,
        "family_count": len(families),
        "animation_count": len(all_animations),
        "frame_count": sum(len(animation["frames"]) for animation in all_animations),
        "facts": {
            "dimensions": "16x16",
            "frames_per_animation": 4,
            "idle_animations_loop": True,
            "collected_animations_loop": False,
            "stock_destroy_effects_used": False,
            "main_ts_is_empty": True,
            "asset_pack_enabled": True,
        },
        "families": manifest_families,
    }
    (ROOT / "animation-manifest.json").write_text(json.dumps(manifest, indent=4) + "\n", encoding="utf-8")


def validate(families: list[dict]) -> None:
    assert len(families) == 12
    assert len({family["id"] for family in families}) == 12
    for family in families:
        for state in ("idle", "collected"):
            frames = family[state]
            assert len(frames) == 4
            assert len({tuple(tuple(row) for row in frame) for frame in frames}) >= 3
            for frame in frames:
                assert len(frame) == SIZE and all(len(row) == SIZE for row in frame)
                assert all(0 <= value <= 15 for row in frame for value in row)
        assert sum(value != 0 for row in family["collected"][-1] for value in row) <= 8


def make_zip() -> None:
    package = ROOT / "Platformer-Animated-Collectibles-v0.0.1.zip"
    if package.exists():
        package.unlink()
    roots = ["README.md", "LICENSE", "pxt.json", "main.ts", "main.blocks", "test.ts", "assets.json", "images.g.jres", "images.g.ts", "tsconfig.json", "animation-manifest.json", "ANIMATION_ASCII.md", "contact-sheet.png", "collectibles-preview.gif", "build_collectibles.py", ".gitignore"]
    with zipfile.ZipFile(package, "w", zipfile.ZIP_DEFLATED) as archive:
        for name in roots:
            archive.write(ROOT / name, name)
        for folder in (FRAME_DIR, PREVIEW_DIR):
            for path in sorted(folder.rglob("*")):
                if path.is_file():
                    archive.write(path, str(path.relative_to(ROOT)).replace("\\", "/"))


def main() -> None:
    families = build_families()
    validate(families)
    write_project_files(families)
    write_frames_and_manifest(families)
    make_contact_sheet(families)
    make_animated_previews(families)
    make_zip()
    print(f"Built {len(families)} collectible families, 24 animations, and 96 exact 16x16 frames in {ROOT}")


if __name__ == "__main__":
    main()
