"""Minimal Conway's Game of Life TUI using only the standard library."""

from __future__ import annotations

import argparse
import curses
import random
import time
from typing import Dict, List, Optional, Tuple


Grid = List[List[bool]]


ALIVE = "■ "
DEAD = "  "
CELL_WIDTH = 2
TICK_SECONDS = 0.12
MIN_SEED_CELLS = 16
MAX_SEED_CELLS = 64

Pattern = List[str]
PATTERNS: Dict[str, Pattern] = {
    "block": [
        "11",
        "11",
    ],
    "blinker": [
        "111",
    ],
    "toad": [
        "0111",
        "1110",
    ],
    "beacon": [
        "1100",
        "1100",
        "0011",
        "0011",
    ],
    "glider": [
        "010",
        "001",
        "111",
    ],
    "lwss": [
        "01101",
        "10001",
        "00001",
        "10010",
    ],
    "gosper_glider_gun": [
        "000000000000000000000000100000000000",
        "000000000000000000000010100000000000",
        "000000000000110000001100000000000011",
        "000000000001000100001100000000000011",
        "110000000010000010001100000000000000",
        "110000000010001011000010100000000000",
        "000000000010000010000000100000000000",
        "000000000001000100000000000000000000",
        "000000000000110000000000000000000000",
    ],
}


def make_grid(height: int, width: int) -> Grid:
    return [[False for _ in range(width)] for _ in range(height)]


def get_grid_size(max_y: int, max_x: int) -> Tuple[int, int]:
    return max(5, max_y - 2), max(10, (max_x - 1) // CELL_WIDTH)


def clear_grid(grid: Grid) -> None:
    for row in grid:
        for index in range(len(row)):
            row[index] = False


def center_seed_area(height: int, width: int) -> Tuple[int, int, int, int]:
    area_height = max(4, height // 3)
    area_width = max(8, width // 3)
    start_row = max(0, (height - area_height) // 2)
    start_col = max(0, (width - area_width) // 2)
    end_row = min(height, start_row + area_height)
    end_col = min(width, start_col + area_width)
    return start_row, end_row, start_col, end_col


def randomize_grid(grid: Grid) -> None:
    height = len(grid)
    width = len(grid[0]) if height else 0

    clear_grid(grid)

    if not height or not width:
        return

    start_row, end_row, start_col, end_col = center_seed_area(height, width)
    positions = [
        (row, col)
        for row in range(start_row, end_row)
        for col in range(start_col, end_col)
    ]
    if not positions:
        return

    seed_count = random.randint(MIN_SEED_CELLS, MAX_SEED_CELLS)
    seed_count = min(seed_count, len(positions))

    for row, col in random.sample(positions, seed_count):
        grid[row][col] = True


def pattern_size(pattern_name: str) -> Tuple[int, int]:
    pattern = PATTERNS[pattern_name]
    return len(pattern), max(len(row) for row in pattern)


def pattern_fits(pattern_name: str, height: int, width: int) -> bool:
    pattern_height, pattern_width = pattern_size(pattern_name)
    return pattern_height <= height and pattern_width <= width


def place_pattern(grid: Grid, pattern_name: str) -> Tuple[int, int]:
    height = len(grid)
    width = len(grid[0]) if height else 0
    pattern = PATTERNS[pattern_name]
    pattern_height = len(pattern)
    pattern_width = max(len(row) for row in pattern)
    if pattern_height > height or pattern_width > width:
        raise ValueError(
            f"pattern '{pattern_name}' needs at least {pattern_width}x{pattern_height} cells"
        )

    clear_grid(grid)

    start_row = max(0, (height - pattern_height) // 2)
    start_col = max(0, (width - pattern_width) // 2)

    for row_offset, row in enumerate(pattern):
        for col_offset, cell in enumerate(row):
            grid_row = start_row + row_offset
            grid_col = start_col + col_offset
            if grid_row < height and grid_col < width and cell == "1":
                grid[grid_row][grid_col] = True

    cursor_row = min(height - 1, start_row + pattern_height // 2)
    cursor_col = min(width - 1, start_col + pattern_width // 2)
    return cursor_row, cursor_col


def resize_grid(grid: Grid, new_height: int, new_width: int) -> Grid:
    resized = make_grid(new_height, new_width)
    copy_height = min(len(grid), new_height)
    copy_width = min(len(grid[0]) if grid else 0, new_width)

    for row in range(copy_height):
        for col in range(copy_width):
            resized[row][col] = grid[row][col]

    return resized


def count_neighbors(grid: Grid, row: int, col: int) -> int:
    height = len(grid)
    width = len(grid[0]) if height else 0
    total = 0

    for row_offset in (-1, 0, 1):
        for col_offset in (-1, 0, 1):
            if row_offset == 0 and col_offset == 0:
                continue

            neighbor_row = row + row_offset
            neighbor_col = col + col_offset
            if 0 <= neighbor_row < height and 0 <= neighbor_col < width:
                total += 1 if grid[neighbor_row][neighbor_col] else 0

    return total


def step_grid(grid: Grid) -> Grid:
    height = len(grid)
    width = len(grid[0]) if height else 0
    next_grid = make_grid(height, width)

    for row in range(height):
        for col in range(width):
            neighbors = count_neighbors(grid, row, col)
            alive = grid[row][col]
            next_grid[row][col] = neighbors == 3 or (alive and neighbors == 2)

    return next_grid


def draw(
    stdscr: "curses._CursesWindow",
    grid: Grid,
    running: bool,
    generation: int,
    cursor_row: int,
    cursor_col: int,
    current_pattern: str,
    status_message: str,
) -> None:
    stdscr.erase()
    max_y, max_x = stdscr.getmaxyx()
    status = (
        f"Conway's Life | {'RUN' if running else 'PAUSE'} | gen={generation} "
        f"| pattern={current_pattern} | "
        "arrows move space/edit s start/pause enter toggle r random c clear q quit"
    )
    stdscr.addnstr(0, 0, status, max_x - 1)
    if status_message and max_y > 1:
        stdscr.addnstr(max_y - 1, 0, status_message, max_x - 1)

    drawable_height = min(len(grid), max(0, max_y - 2))
    drawable_width = min(len(grid[0]) if grid else 0, max(1, (max_x - 1) // CELL_WIDTH))

    for row in range(drawable_height):
        for col in range(drawable_width):
            cell_text = ALIVE if grid[row][col] else DEAD
            attr = (
                curses.A_REVERSE
                if (not running and row == cursor_row and col == cursor_col)
                else curses.A_NORMAL
            )
            stdscr.addnstr(row + 1, col * CELL_WIDTH, cell_text, CELL_WIDTH, attr)

    stdscr.refresh()


def run(stdscr: "curses._CursesWindow", initial_pattern: Optional[str]) -> None:
    try:
        curses.curs_set(0)
    except curses.error:
        pass
    stdscr.keypad(True)
    stdscr.nodelay(True)
    stdscr.timeout(10)

    max_y, max_x = stdscr.getmaxyx()
    grid_height, grid_width = get_grid_size(max_y, max_x)

    grid = make_grid(grid_height, grid_width)
    running = False
    generation = 0
    cursor_row = grid_height // 2
    cursor_col = grid_width // 2
    current_pattern = "empty"
    status_message = ""
    if initial_pattern:
        if pattern_fits(initial_pattern, grid_height, grid_width):
            cursor_row, cursor_col = place_pattern(grid, initial_pattern)
            current_pattern = initial_pattern
        else:
            pattern_height, pattern_width = pattern_size(initial_pattern)
            status_message = (
                f"pattern '{initial_pattern}' too large for board "
                f"{grid_width}x{grid_height}; needs {pattern_width}x{pattern_height}"
            )
    last_tick = time.monotonic()

    while True:
        max_y, max_x = stdscr.getmaxyx()
        next_height, next_width = get_grid_size(max_y, max_x)
        if next_height != grid_height or next_width != grid_width:
            grid = resize_grid(grid, next_height, next_width)
            grid_height = next_height
            grid_width = next_width
            cursor_row = min(cursor_row, grid_height - 1)
            cursor_col = min(cursor_col, grid_width - 1)
            if current_pattern not in {"empty", "random", "custom"} and not pattern_fits(
                current_pattern, grid_height, grid_width
            ):
                status_message = (
                    f"pattern '{current_pattern}' no longer fits resized board "
                    f"{grid_width}x{grid_height}"
                )

        draw(
            stdscr,
            grid,
            running,
            generation,
            cursor_row,
            cursor_col,
            current_pattern,
            status_message,
        )
        key = stdscr.getch()

        if key in (ord("q"), ord("Q")):
            return
        if key == curses.KEY_RESIZE:
            continue
        if key == curses.KEY_UP:
            cursor_row = max(0, cursor_row - 1)
        elif key == curses.KEY_DOWN:
            cursor_row = min(grid_height - 1, cursor_row + 1)
        elif key == curses.KEY_LEFT:
            cursor_col = max(0, cursor_col - 1)
        elif key == curses.KEY_RIGHT:
            cursor_col = min(grid_width - 1, cursor_col + 1)
        elif key in (ord(" "), curses.KEY_ENTER, 10, 13):
            grid[cursor_row][cursor_col] = not grid[cursor_row][cursor_col]
            current_pattern = "custom"
            status_message = ""
        elif key in (ord("s"), ord("S")):
            running = not running
            last_tick = time.monotonic()
            status_message = ""
        elif key in (ord("r"), ord("R")):
            randomize_grid(grid)
            generation = 0
            running = False
            cursor_row = grid_height // 2
            cursor_col = grid_width // 2
            current_pattern = "random"
            status_message = ""
            last_tick = time.monotonic()
        elif key in (ord("c"), ord("C")):
            clear_grid(grid)
            generation = 0
            running = False
            current_pattern = "empty"
            status_message = ""
            last_tick = time.monotonic()

        now = time.monotonic()
        if running and now - last_tick >= TICK_SECONDS:
            grid = step_grid(grid)
            generation += 1
            last_tick = now


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Conway's Game of Life TUI")
    parser.add_argument(
        "--pattern",
        choices=sorted(PATTERNS),
        help="load a built-in pattern at startup",
    )
    parser.add_argument(
        "--list-patterns",
        action="store_true",
        help="print available built-in patterns and exit",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.list_patterns:
        for pattern_name in sorted(PATTERNS):
            print(pattern_name)
        return

    curses.wrapper(run, args.pattern)


if __name__ == "__main__":
    main()
