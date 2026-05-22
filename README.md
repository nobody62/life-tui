# life-tui

A minimal Conway's Game of Life TUI written in Python using only the standard library.

## Requirements

- Python 3.9+
- A terminal with `curses` support

## Run

```bash
python life_tui.py
```

Use a built-in preset:

```bash
python life_tui.py --pattern glider
python life_tui.py --pattern gosper_glider_gun
```

List available presets:

```bash
python life_tui.py --list-patterns
```

## Controls

- `Arrow keys`: move cursor
- `Space` / `Enter`: toggle the current cell
- `s`: start or pause
- `r`: randomize a centered seed
- `c`: clear the board
- `q`: quit

## Built-in Patterns

- `block`
- `blinker`
- `toad`
- `beacon`
- `glider`
- `lwss`
- `gosper_glider_gun`
