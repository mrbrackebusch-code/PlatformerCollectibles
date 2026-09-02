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
    liquid_surfaces = (
        {x: 9 for x in range(3, 13)},
        {x: 8 if x <= 6 else 9 if x <= 9 else 10 for x in range(3, 13)},
        {x: 9 for x in range(3, 13)},
        {x: 10 if x <= 5 else 9 if x <= 8 else 8 for x in range(3, 13)},
    )
    surface = liquid_surfaces[phase]
    for x in range(3, 13):
        top = surface[x] + dy
        for y in range(top, 14 + dy):
            if (x, y) in body and frame[y][x] != 8:
                frame[y][x] = 10
        if (x, top) in body and frame[top][x] != 8:
            frame[top][x] = 3
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


def draw_swinging_berries(sway: int, phase: int) -> list[list[int]]:
    frame = blank()
    left_center = 5 + sway
    right_center = 10 + sway
    left = mask_ellipse(left_center, 9, 3.5, 3.5)
    right = mask_ellipse(right_center, 9, 3.5, 3.5)
    paint_mask(frame, left, 14, 2)
    paint_mask(frame, right, 14, 2)
    pixel(frame, left_center - 1, 7, 3)
    pixel(frame, right_center - 1, 7, 3)
    # The top of the stems stays fixed while the fruit swings underneath it.
    line(frame, left_center, 6, 7, 2, 7)
    line(frame, right_center, 6, 7, 2, 7)
    leaf_direction = -1 if sway < 0 else 1 if sway > 0 else (1 if phase == 1 else 0)
    leaf_x = 8 + leaf_direction
    rect(frame, leaf_x, 2, leaf_x + 2, 3, 7)
    pixel(frame, left_center - 2, 8, 1)
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


def draw_candy(phase: int) -> list[list[int]]:
    frame = blank()
    left_tip = (0, -1, 0, 1)[phase]
    right_tip = -left_tip
    left_wrapper = mask_polygon([(0.5, 4.5 + left_tip), (4.5, 6), (4.5, 10), (0.5, 11.5 + left_tip), (1.5, 8)])
    right_wrapper = mask_polygon([(15.5, 4.5 + right_tip), (11.5, 6), (11.5, 10), (15.5, 11.5 + right_tip), (14.5, 8)])
    paint_mask(frame, left_wrapper, 14, 5)
    paint_mask(frame, right_wrapper, 14, 5)
    body = mask_ellipse(7.5, 7.5, 4.5, 4)
    paint_mask(frame, body, 14, 3)
    stripe_x = (6, 7, 8, 7)[phase]
    for y in range(5, 11):
        if (stripe_x, y) in body and frame[y][stripe_x] != 14:
            frame[y][stripe_x] = 5
    pixel(frame, 6, 5, 1)
    if phase == 2:
        pixel(frame, 13, 3, 3)
    return frame


def ring(frame: list[list[int]], radius: int, color: int, phase: int = 0) -> None:
    cx = cy = 7.5
    for y in range(SIZE):
        for x in range(SIZE):
            distance = math.hypot(x - cx, y - cy)
            if abs(distance - radius) < 0.55 and (x + y + phase) % 2 == 0:
                pixel(frame, x, y, color)


def scaled_sprite(frame: list[list[int]], width: int, height: int, center_x: float = 7.5, center_y: float = 7.5) -> list[list[int]]:
    points = [(x, y) for y, row in enumerate(frame) for x, value in enumerate(row) if value]
    if not points:
        return blank()
    min_x = min(x for x, _ in points)
    max_x = max(x for x, _ in points)
    min_y = min(y for _, y in points)
    max_y = max(y for _, y in points)
    source_width = max_x - min_x + 1
    source_height = max_y - min_y + 1
    result = blank()
    left = round(center_x - (width - 1) / 2)
    top = round(center_y - (height - 1) / 2)
    for target_y in range(height):
        source_y = min_y + min(source_height - 1, int(target_y * source_height / height))
        for target_x in range(width):
            source_x = min_x + min(source_width - 1, int(target_x * source_width / width))
            value = frame[source_y][source_x]
            if value:
                pixel(result, left + target_x, top + target_y, value)
    return result


def tiny_heart(frame: list[list[int]], x: int, y: int) -> None:
    for dx, dy, color in ((-1, 0, 3), (1, 0, 3), (-2, 1, 2), (0, 1, 2), (2, 1, 2), (-1, 2, 2), (0, 2, 2), (1, 2, 2), (0, 3, 2)):
        pixel(frame, x + dx, y + dy, color)


def item_specific_collected(style: str, idle: list[list[list[int]]]) -> list[list[list[int]]]:
    base = idle[0]
    if style == "coin":
        first = clone(base)
        sparkle(first, 13, 2, 1)
        second = shift(draw_coin(6, True), 0, -2)
        line(second, 4, 12, 5, 10, 4)
        line(second, 11, 12, 10, 10, 5)
        third = shift(draw_coin(2), 0, -4)
        for x, y, color in ((5, 11, 4), (10, 10, 5), (6, 13, 5), (11, 13, 4)):
            pixel(third, x, y, color)
        fourth = blank()
        for x, y, color in ((7, 1, 1), (4, 6, 5), (11, 5, 4), (7, 10, 5)):
            pixel(fourth, x, y, color)
        return [first, second, third, fourth]

    if style == "orb":
        first = clone(base)
        sparkle(first, 13, 4, 9)
        second = scaled_sprite(base, 10, 10)
        for x, y in ((7, 1), (14, 7), (8, 14), (1, 8)):
            pixel(second, x, y, 9)
        third = scaled_sprite(base, 5, 5)
        ring(third, 5, 9)
        fourth = blank()
        for x, y, color in ((7, 5, 1), (4, 8, 9), (10, 8, 6), (7, 11, 8)):
            pixel(fourth, x, y, color)
        return [first, second, third, fourth]

    if style == "gem":
        first = clone(base)
        sparkle(first, 13, 2, 9)
        second = clone(base)
        line(second, 7, 4, 8, 8, 8)
        line(second, 8, 8, 5, 11, 8)
        third = blank()
        for x, y, color in ((5, 4, 1), (4, 5, 9), (11, 4, 9), (12, 5, 6), (4, 11, 6), (6, 12, 9), (11, 11, 1), (10, 12, 9)):
            pixel(third, x, y, color)
        fourth = blank()
        for x, y, color in ((2, 2, 9), (13, 3, 1), (12, 13, 6), (3, 12, 9)):
            pixel(fourth, x, y, color)
        return [first, second, third, fourth]

    if style == "star":
        first = clone(base)
        sparkle(first, 14, 2, 1)
        second = clone(idle[1])
        for x, y in ((7, 0), (15, 7), (8, 15), (0, 8)):
            pixel(second, x, y, 5)
        third = blank()
        sparkle(third, 7, 7, 5, 3)
        pixel(third, 7, 7, 1)
        fourth = blank()
        for x, y, color in ((7, 1, 5), (14, 7, 4), (8, 14, 5), (1, 8, 4)):
            pixel(fourth, x, y, color)
        return [first, second, third, fourth]

    if style == "heart":
        first = clone(base)
        pixel(first, 12, 3, 3)
        second = clone(idle[1])
        third = blank()
        tiny_heart(third, 5, 6)
        tiny_heart(third, 10, 5)
        fourth = blank()
        for x, y, color in ((4, 3, 3), (6, 5, 2), (10, 2, 3), (12, 4, 2)):
            pixel(fourth, x, y, color)
        return [first, second, third, fourth]

    if style == "key":
        first = clone(base)
        sparkle(first, 13, 3, 5)
        second = shift(mirror(base), 0, -1)
        pixel(second, 3, 12, 4)
        third = scaled_sprite(base, 8, 7, 8, 5)
        for x, y in ((4, 11), (10, 10), (12, 8)):
            pixel(third, x, y, 5)
        fourth = blank()
        for x, y, color in ((7, 1, 1), (12, 4, 5), (11, 9, 4), (4, 12, 5)):
            pixel(fourth, x, y, color)
        return [first, second, third, fourth]

    if style == "potion":
        first = clone(base)
        pixel(first, 11, 3, 10)
        second = clone(base)
        rect(second, 6, 1, 9, 2, 0)
        rect(second, 7, 0, 8, 1, 14)
        for x, y, color in ((5, 4, 3), (10, 3, 10), (12, 6, 9)):
            pixel(second, x, y, color)
        third = blank()
        for x, y, color in ((4, 10, 8), (3, 12, 9), (11, 10, 8), (12, 12, 9), (6, 8, 10), (9, 7, 3), (7, 4, 10), (11, 3, 3)):
            pixel(third, x, y, color)
        fourth = blank()
        for x, y, color in ((5, 8, 10), (8, 5, 3), (11, 2, 10), (13, 7, 9)):
            pixel(fourth, x, y, color)
        return [first, second, third, fourth]

    if style == "berries":
        first = clone(base)
        sparkle(first, 12, 4, 3)
        second = scaled_sprite(base, 12, 8, 7.5, 10)
        third = blank()
        for x, y, color in ((4, 7, 2), (3, 9, 3), (6, 11, 2), (11, 7, 3), (12, 9, 2), (9, 12, 2), (7, 5, 7), (9, 4, 7)):
            pixel(third, x, y, color)
        fourth = blank()
        for x, y, color in ((2, 5, 2), (5, 11, 3), (10, 3, 7), (13, 7, 2)):
            pixel(fourth, x, y, color)
        return [first, second, third, fourth]

    if style == "gear":
        first = clone(base)
        pixel(first, 13, 3, 1)
        second = draw_gear(1)
        sparkle(second, 2, 12, 11)
        third = scaled_sprite(draw_gear(2), 8, 8, 8, 5)
        for x, y in ((4, 11), (11, 10), (13, 7)):
            pixel(third, x, y, 11)
        fourth = blank()
        for x, y, color in ((2, 3, 11), (13, 3, 12), (12, 12, 11), (3, 13, 1)):
            pixel(fourth, x, y, color)
        return [first, second, third, fourth]

    if style == "battery":
        first = draw_battery(0, 2)
        sparkle(first, 13, 4, 9)
        second = clone(first)
        rect(second, 6, 0, 9, 2, 9)
        rect(second, 7, 0, 8, 1, 1)
        third = blank()
        line(third, 7, 13, 9, 9, 8)
        line(third, 9, 9, 6, 6, 9)
        line(third, 6, 6, 8, 2, 1)
        pixel(third, 5, 11, 6)
        pixel(third, 10, 5, 6)
        fourth = blank()
        for x, y, color in ((8, 1, 1), (5, 5, 9), (10, 7, 6), (7, 11, 9)):
            pixel(fourth, x, y, color)
        return [first, second, third, fourth]

    if style == "crown":
        first = clone(base)
        sparkle(first, 14, 2, 1)
        second = shift(base, 0, -2)
        pixel(second, 3, 13, 5)
        pixel(second, 12, 13, 10)
        third = scaled_sprite(base, 8, 7, 7.5, 4.5)
        for x, y, color in ((4, 11, 5), (8, 12, 10), (11, 10, 5)):
            pixel(third, x, y, color)
        fourth = blank()
        for x, y, color in ((7, 1, 1), (3, 5, 5), (12, 4, 5), (8, 9, 10)):
            pixel(fourth, x, y, color)
        return [first, second, third, fourth]

    if style == "candy":
        first = clone(base)
        sparkle(first, 13, 2, 1)
        second = draw_candy(2)
        pixel(second, 1, 3, 5)
        pixel(second, 14, 12, 5)
        third = scaled_sprite(base, 6, 5)
        for x, y, color in ((1, 4, 5), (3, 6, 4), (14, 4, 5), (12, 6, 4), (2, 11, 5), (13, 11, 5)):
            pixel(third, x, y, color)
        fourth = blank()
        for x, y, color in ((3, 3, 5), (7, 6, 3), (11, 2, 1), (13, 9, 4)):
            pixel(fourth, x, y, color)
        return [first, second, third, fourth]

    raise ValueError(style)


def build_families() -> list[dict]:
    families = [
        {"id": "coin", "name": "Spinning Coin", "idle_ms": 120, "colors": (5, 1, 4), "idle": [draw_coin(10), draw_coin(6), draw_coin(2), draw_coin(6, True)]},
        {"id": "orb", "name": "Orbiting Energy Orb", "idle_ms": 150, "colors": (9, 1, 8), "idle": [shift(draw_orb(0, phase), dx, dy) for phase, (dx, dy) in enumerate(((0, -1), (1, 0), (0, 1), (-1, 0)))]},
        {"id": "gem", "name": "Shimmering Crystal", "idle_ms": 140, "colors": (9, 1, 6), "idle": [shift(draw_gem(0, phase), dx, dy) for phase, (dx, dy) in enumerate(((0, -1), (1, 0), (0, 1), (-1, 0)))]},
        {"id": "star", "name": "Pulsing Star", "idle_ms": 130, "colors": (5, 1, 4), "idle": [draw_star(phase) for phase in range(4)]},
        {"id": "heart", "name": "Orbiting Heart", "idle_ms": 150, "colors": (2, 1, 3), "idle": [shift(draw_heart(1.0, 0, phase), dx, dy) for phase, (dx, dy) in enumerate(((0, -1), (-1, 0), (0, 1), (1, 0)))]},
        {"id": "key", "name": "Swaying Key", "idle_ms": 150, "colors": (5, 1, 14), "idle": [shift(draw_key(0, phase), dx, 0) for phase, dx in enumerate((-1, 0, 1, 0))]},
        {"id": "potion", "name": "Bubbling Potion", "idle_ms": 160, "colors": (10, 3, 8), "idle": [draw_potion(0, phase) for phase in range(4)]},
        {"id": "berries", "name": "Swinging Berries", "idle_ms": 150, "colors": (2, 3, 7), "idle": [draw_swinging_berries(sway, phase) for phase, sway in enumerate((-1, 0, 1, 0))]},
        {"id": "gear", "name": "Turning Gear", "idle_ms": 120, "colors": (11, 1, 12), "idle": [draw_gear(phase) for phase in range(4)]},
        {"id": "battery", "name": "Pulsing Energy Cell", "idle_ms": 140, "colors": (9, 1, 8), "idle": [draw_battery(0, phase) for phase in range(4)]},
        {"id": "crown", "name": "Gliding Crown", "idle_ms": 150, "colors": (5, 1, 14), "idle": [shift(draw_crown(0, phase), dx, 0) for phase, dx in enumerate((0, 1, 0, -1))]},
        {"id": "candy", "name": "Wrapped Candy", "idle_ms": 160, "colors": (3, 1, 5), "idle": [draw_candy(phase) for phase in range(4)]},
    ]
    for family in families:
        family["collected"] = item_specific_collected(family["id"], family["idle"])
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
    cell_width = 128
    cell_height = 128
    for animation_name, frame_index, duration in timeline:
        canvas = Image.new("RGB", (columns * cell_width, 3 * cell_height), "#171320")
        draw = ImageDraw.Draw(canvas)
        for family_index, family in enumerate(families):
            row, col = divmod(family_index, columns)
            left = col * cell_width
            top = row * cell_height
            draw.rectangle((left + 4, top + 4, left + cell_width - 5, top + cell_height - 5), fill="#211a2a", outline="#3d304a", width=1)
            selected = family[animation_name][frame_index]
            sprite = image_from_frame(selected).resize((112, 112), Image.Resampling.NEAREST)
            canvas.paste(sprite, (left + 8, top + 8), sprite)
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

Included collectibles: spinning coin, energy orb, crystal, star, heart, key, potion, berries, gear, energy cell, crown, and wrapped candy.

## Use in MakeCode Arcade

After this folder is published as a public GitHub repository, add its GitHub URL through **Settings → Extensions**. Because `assetPack` is enabled, the named animations appear in the Animation gallery and the pack's code is ignored.

For each item, choose the matching `Idle` and `Collected` animations. Loop the idle animation. Run the collected animation once, then destroy or hide the collectible after the final frame. Each collected sequence preserves the item's identity: coins flip away, orbs contract, crystals split into shards, hearts release tiny hearts, potions pop into bubbles, batteries discharge, and candies unwrap into sugar sparkles. No stock destroyed effect is needed.

Suggested timing is recorded in `animation-manifest.json`. Idle loops use 120–170 ms per frame; collected animations use 75 ms per frame and should not loop.

## Contents

- `images.g.jres` / `images.g.ts`: MakeCode animation assets
- `test.ts`: compile-only resolution check for all 24 named animations
- `contact-sheet.png`: every exact frame at readable scale
- `collectibles-preview.gif`: simple montage of every idle and collected animation
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
