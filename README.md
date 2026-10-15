# Match-3 Gem Swap Repair Lab

This project is a grid-based match-3 puzzle game using **Pygame**. It introduces students to 2D matrix manipulation, animated tile gravity, adjacent swap validation, recursive match resolution, and move-budget turn constraints within an object-oriented codebase.
---

## What's Provided

A working Match-3 Gem Swap game with:

- An 8x8 procedural gem grid with smooth vertical dropping animations
- Click-to-select and adjacent gem swapping mechanics
- Horizontal and vertical 3-in-a-row detection with automatic drop-and-refill resolution
- Score tracking, move budgeting, and win/loss overlay states

It has **one deliberate bug** and **three optional features** left as tasks to implement. You are expected to **analyze**, **interact with an AI assistant**, and **complete/fix** the game to make it fully functional and more interesting.

### **Use an LLM (e.g. ChatGPT or Claude) as your debugging and pair-programming partner for this lab.**
---

## Getting Started

### Setup

1. Make sure you have Python 3.10+ installed.
2. Install dependencies:

```bash
pip install pygame
```

3. Run the game:

```bash
python main.py
```

**Controls:** Left-click two adjacent gems to swap them. Press R to restart.

## Completed Implementation

All four tasks below are implemented in the current game:

- Invalid swaps revert without spending a move.
- A successful swap spends one move, including all its cascades. Match waves score
  at x1, x2, x3, and so on; each new successful swap starts at x1. The HUD shows
  the multiplier and points from the latest wave. Falling gems settle between waves.
- Matching four or more gems creates a glowing striped gem. Horizontal matches
  create row clears; vertical matches create column clears. Matching a striped
  gem clears that entire line, including other specials caught in the blast.
  The surviving special is not counted as a cleared gem for scoring.
- After more than five seconds without mouse or keyboard input, an available swap
  pair pulses. Input clears the hint; hints do not appear during falls or game over.

The startup crash was fixed separately by restoring the missing column loop in
`drop_and_refill()`. Win/loss overlays wait for the final cascade to finish.

### Before and After Videos

- [Before: 10 seconds](recordings/before.mp4)
- [After: 10 seconds](recordings/after.mp4)

These are recordings of the actual game renderer with scripted clicks and
reproducible board setups. The before recording includes only the startup repair;
all four task behaviors are still unfixed in that version. See
[recording notes](recordings/README.md) for timing, source snapshots, and reproduction.


## Tasks to Complete

Each task must be completed using an iterative process involving LLM suggestions and your critical code review.

### Task 1: Fix the invalid swap move deduction bug

Swapping two gems that do not form any 3-in-a-row combination reverts the gems back to their original tiles, yet the game still docks a remaining move. Ensure moves are only deducted when a swap successfully creates at least one valid match.

### Task 2: Implement cascade combo multiplier

Gems currently award a flat point value regardless of whether they were matched by the player or cleared via gravity chain reactions. Introduce a cascade combo multiplier that increases score rewards sequentially for every consecutive falling reaction triggered within a single turn.

### Task 3: Implement 4-in-a-row special line-clear gems

Standard match-3 games reward larger combinations. Aligning 4 matching gems in a line should merge them into an enhanced glowing gem that detonates an entire row or column when subsequently matched.

### Task 4:Implement an idle hint indicator

Players can occasionally get stuck scanning for potential combinations. If no input is registered for more than 5 seconds, highlight an available adjacent swap pair with a subtle pulsing or shimmering animation to guide the player forward.

---

## Expected Behavior

- Clicking two adjacent gems swaps them.
- If a swap creates 3 or more matching gems in a row or column, the matched gems clear, higher gems fall down, new gems populate the top, and remaining moves decrease by 1
- If a swap produces no matches, gems revert to their prior positions and the move counter does not decrease.
- Reaching 500 points triggers the STAGE CLEARED! win banner; running out of moves triggers OUT OF MOVES!
---

## Folder Structure

```
match_three_gem/
├── game/
│   ├── board.py
│   └── game_engine.py
├── main.py
└── README.md
```

---

## Submission Checklist

Submission is only the following three things:

- [] A 10-second video of gameplay **before** your changes, showing the bug/broken behavior
- [] A 10-second video of gameplay **after** your changes, showing the bug fixed and the new features working
- [] The Chat/LLM used page link, with the complete chat history
