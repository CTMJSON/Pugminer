#!/usr/bin/env python3
"""Utility to update MinerScreen images with a custom Pugminer logo."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

ROOT = Path(__file__).resolve().parents[1]
MEDIA = ROOT / "src" / "media"

FONT_PATTERNS: Dict[str, Tuple[str, ...]] = {
    "P": (
        "#####",
        "#...#",
        "#####",
        "#....",
        "#....",
        "#....",
        "#....",
    ),
    "U": (
        "#...#",
        "#...#",
        "#...#",
        "#...#",
        "#...#",
        "#...#",
        "#####",
    ),
    "G": (
        ".####",
        "#....",
        "#....",
        "#.###",
        "#...#",
        "#...#",
        ".###.",
    ),
    "M": (
        "#...#",
        "##.##",
        "#.#.#",
        "#.#.#",
        "#...#",
        "#...#",
        "#...#",
    ),
    "I": (
        "#####",
        "..#..",
        "..#..",
        "..#..",
        "..#..",
        "..#..",
        "#####",
    ),
    "N": (
        "#...#",
        "##..#",
        "#.#.#",
        "#..##",
        "#..##",
        "#...#",
        "#...#",
    ),
    "E": (
        "#####",
        "#....",
        "####.",
        "#....",
        "#....",
        "#....",
        "#####",
    ),
    "R": (
        "#####",
        "#...#",
        "#...#",
        "####.",
        "#..#.",
        "#...#",
        "#...#",
    ),
}
FONT_WIDTH = 5
FONT_HEIGHT = 7


def rgb_to_565(r: int, g: int, b: int) -> int:
    r5 = (r * 31 + 127) // 255
    g6 = (g * 63 + 127) // 255
    b5 = (b * 31 + 127) // 255
    return (r5 << 11) | (g6 << 5) | b5


COLORS = {
    "border": rgb_to_565(240, 240, 240),
    "outer_bg": rgb_to_565(14, 14, 18),
    "inner_bg": rgb_to_565(28, 28, 34),
    "accent": rgb_to_565(196, 160, 64),
    "left_pug": rgb_to_565(70, 62, 58),
    "right_pug": rgb_to_565(212, 200, 178),
    "text": rgb_to_565(248, 248, 248),
}


class LogoCanvas:
    def __init__(self, pixels: List[int], width: int, height: int) -> None:
        self.pixels = pixels
        self.width = width
        self.height = height

    def set_pixel(self, x: int, y: int, value: int) -> None:
        if 0 <= x < self.width and 0 <= y < self.height:
            self.pixels[y * self.width + x] = value

    def fill_rect(self, x0: int, y0: int, x1: int, y1: int, value: int) -> None:
        for y in range(max(0, y0), min(self.height, y1)):
            start = y * self.width + max(0, x0)
            end = y * self.width + min(self.width, x1)
            for idx in range(start, end):
                self.pixels[idx] = value

    def draw_border(self, x0: int, y0: int, x1: int, y1: int, value: int, thickness: int = 1) -> None:
        for t in range(thickness):
            self.fill_rect(x0 + t, y0 + t, x1 - t, y0 + t + 1, value)
            self.fill_rect(x0 + t, y1 - t - 1, x1 - t, y1 - t, value)
            self.fill_rect(x0 + t, y0 + t, x0 + t + 1, y1 - t, value)
            self.fill_rect(x1 - t - 1, y0 + t, x1 - t, y1 - t, value)

    def draw_circle(self, cx: int, cy: int, radius: int, value: int) -> None:
        r_sq = radius * radius
        for y in range(cy - radius, cy + radius + 1):
            for x in range(cx - radius, cx + radius + 1):
                if (x - cx) ** 2 + (y - cy) ** 2 <= r_sq:
                    self.set_pixel(x, y, value)

    def draw_text(self, text: str, x: int, y: int, scale: int, value: int) -> None:
        cursor_x = x
        for ch in text:
            pattern = FONT_PATTERNS.get(ch)
            if not pattern:
                cursor_x += scale * (FONT_WIDTH + 1)
                continue
            for row, row_pattern in enumerate(pattern):
                for col, cell in enumerate(row_pattern):
                    if cell == '#':
                        for dy in range(scale):
                            for dx in range(scale):
                                self.set_pixel(cursor_x + col * scale + dx, y + row * scale + dy, value)
            cursor_x += scale * (FONT_WIDTH + 1)


def update_pixels_with_logo(pixels: List[int], width: int, height: int) -> None:
    canvas = LogoCanvas(pixels, width, height)

    patch_w = max(48, min(int(width * 0.42), width - 4))
    patch_h = max(36, min(int(height * 0.52), height - 4))
    offset_x = max(2, int(width * 0.02))
    offset_y = max(2, int(height * 0.05))
    x0 = offset_x
    y0 = offset_y
    x1 = min(width - 2, x0 + patch_w)
    y1 = min(height - 2, y0 + patch_h)

    canvas.fill_rect(x0, y0, x1, y1, COLORS["outer_bg"])
    border_thickness = max(1, patch_w // 32)
    canvas.draw_border(x0, y0, x1, y1, COLORS["border"], border_thickness)

    inner_margin = max(2, patch_w // 18)
    inner_x0 = x0 + inner_margin
    inner_y0 = y0 + inner_margin
    inner_x1 = x1 - inner_margin
    inner_y1 = y1 - inner_margin
    canvas.fill_rect(inner_x0, inner_y0, inner_x1, inner_y1, COLORS["inner_bg"])

    accent_height = max(3, (inner_y1 - inner_y0) // 8)
    canvas.fill_rect(inner_x0, inner_y0, inner_x1, inner_y0 + accent_height, COLORS["accent"])

    circle_radius = max(4, min((inner_x1 - inner_x0) // 6, (inner_y1 - inner_y0) // 4))
    circle_y = inner_y0 + accent_height + circle_radius + max(1, circle_radius // 4)
    left_cx = inner_x0 + circle_radius + max(1, circle_radius // 2)
    right_cx = inner_x1 - circle_radius - max(1, circle_radius // 2)

    canvas.draw_circle(left_cx, circle_y, circle_radius, COLORS["left_pug"])
    canvas.draw_circle(right_cx, circle_y, circle_radius, COLORS["right_pug"])

    highlight_radius = max(2, circle_radius // 2)
    canvas.draw_circle(left_cx - highlight_radius // 2, circle_y - highlight_radius // 2, highlight_radius, COLORS["inner_bg"])
    canvas.draw_circle(right_cx + highlight_radius // 3, circle_y - highlight_radius // 3, highlight_radius, COLORS["inner_bg"])

    text = "PUGMINER"
    available_width = inner_x1 - inner_x0
    available_height = inner_y1 - circle_y - circle_radius - 2
    if available_width <= 0 or available_height <= 0:
        return

    scale_x = max(1, available_width // (len(text) * (FONT_WIDTH + 1)))
    scale_y = max(1, available_height // (FONT_HEIGHT + 1))
    scale = max(1, min(scale_x, scale_y))

    text_width = scale * len(text) * (FONT_WIDTH + 1)
    text_x = inner_x0 + max(0, (available_width - text_width) // 2)
    text_y = circle_y + circle_radius + max(2, scale)
    if text_y + FONT_HEIGHT * scale > inner_y1:
        text_y = inner_y1 - FONT_HEIGHT * scale - 1

    canvas.draw_text(text, text_x, text_y, scale, COLORS["text"])


def parse_array(values_block: str) -> List[int]:
    cleaned_lines = []
    for line in values_block.splitlines():
        if '//' in line:
            line = line.split('//', 1)[0]
        cleaned_lines.append(line)
    cleaned = '\n'.join(cleaned_lines)
    numbers = re.findall(r"0x[0-9A-Fa-f]+", cleaned)
    return [int(num, 16) for num in numbers]


def format_array(data: Iterable[int]) -> str:
    values = list(data)
    lines: List[str] = []
    for idx in range(0, len(values), 16):
        chunk = values[idx : idx + 16]
        line = ", ".join(f"0x{value:04X}" for value in chunk)
        lines.append(f"{line},")
        next_index = idx + len(chunk)
        lines.append(f"  // 0x{next_index:04X} ({next_index})")
    return "\n".join(lines)


def update_file(path: Path) -> bool:
    content = path.read_text()
    width_match = re.search(r"const uint16_t MinerWidth = (\d+);", content)
    height_match = re.search(r"const uint16_t MinerHeight = (\d+);", content)
    if not width_match or not height_match:
        return False
    width = int(width_match.group(1))
    height = int(height_match.group(1))

    array_match = re.search(
        r"(const unsigned short MinerScreen\[[^\]]+\] PROGMEM\s*=\s*\{)(.*?)(\n\};)",
        content,
        re.DOTALL,
    )
    if not array_match:
        return False

    prefix, values_block, suffix = array_match.groups()
    pixels = parse_array(values_block)
    size_match = re.search(r'\[[^\]]*?(0x[0-9A-Fa-f]+|\d+)[^\]]*\]', prefix)
    if not size_match:
        raise ValueError(f'Unable to determine array length for {path.name}')
    expected_length = int(size_match.group(1), 16 if '0x' in size_match.group(1).lower() else 10)
    if len(pixels) < expected_length:
        raise ValueError(f"Unexpected pixel count in {path.name}: {len(pixels)} < {expected_length}")

    screen = pixels[:expected_length]
    update_pixels_with_logo(screen, width, height)
    formatted = format_array(screen)
    new_block = f"{prefix}\n{formatted}\n}}"
    new_content = content[: array_match.start()] + new_block + suffix + content[array_match.end():]
    path.write_text(new_content)
    return True


def main() -> None:
    updated_files = []
    for path in sorted(MEDIA.glob("images_*_*.h")):
        if update_file(path):
            updated_files.append(path)
    if not updated_files:
        raise SystemExit("No MinerScreen arrays were updated.")
    print("Updated:")
    for path in updated_files:
        print(f" - {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
