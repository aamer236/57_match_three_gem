import argparse
import hashlib
import json
import os
from pathlib import Path
import random
import subprocess
import sys
from unittest.mock import patch
import zipfile

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pygame
from game.board import GEM_COLORS, GRID_SIZE, TILE_SIZE, Gem
from game.game_engine import GameEngine


def special_setup(engine):
    board = engine.board
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            gem = Gem(GEM_COLORS[(row * 2 + col) % 6], row, col)
            gem.current_y = gem.target_y
            board.grid[row][col] = gem
    for row, col, color in [
        (7, 0, 0), (7, 1, 0), (7, 2, 1), (7, 3, 0),
        (7, 4, 4), (6, 2, 0), (5, 1, 0),
    ]:
        board.grid[row][col].color = GEM_COLORS[color]
    assert not board.find_matches()
    random.seed(12)


def click(engine, position):
    row, col = position
    point = (
        engine.board.offset_x + col * TILE_SIZE + TILE_SIZE // 2,
        engine.board.offset_y + row * TILE_SIZE + TILE_SIZE // 2,
    )
    engine.handle_click(point)
    return point


def record(label, output):
    output.mkdir(parents=True, exist_ok=True)
    if (output / f"{label}.mp4").exists():
        raise FileExistsError("Recording already exists; use --output with a new directory.")
    source_paths = [ROOT / name for name in (
        "main.py", "game/board.py", "game/game_engine.py", "tools/record_demo.py"
    )]
    hashes = {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
              for path in source_paths}
    with zipfile.ZipFile(output / f"{label}-source.zip", "w") as archive:
        for path in source_paths:
            archive.write(path, str(path.relative_to(ROOT)))
    pygame.init()
    screen = pygame.display.set_mode((600, 650))
    canvas = pygame.Surface((960, 720))
    title_font = pygame.font.SysFont(None, 30)
    text_font = pygame.font.SysFont(None, 23)
    small_font = pygame.font.SysFont(None, 20)
    encoder = subprocess.Popen([
        "ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo",
        "-pixel_format", "rgb24", "-video_size", "960x720", "-framerate", "60",
        "-i", "pipe:0", "-an", "-c:v", "libx264", "-crf", "18",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        str(output / f"{label}.mp4"),
    ], stdin=subprocess.PIPE)
    evidence = []
    observations = ["Waiting for 5 seconds...", "Pending", "Pending", "Pending"]
    cursor = None
    cursor_frame = -100
    checks = [False] * 4
    with patch("pygame.time.get_ticks") as ticks:
        ticks.return_value = 0
        random.seed(0)
        engine = GameEngine(600, 650)
        for step in range(100):
            engine.update()
        original_moves = engine.board.moves_remaining
        for frame in range(600):
            ticks.return_value = frame * 1000 // 60
            active = 0 if frame < 330 else 1 if frame < 380 else 2 if frame < 490 else 3
            if frame == 380:
                engine = GameEngine(600, 650)
                special_setup(engine)
            if frame == 490:
                random.seed(0)
                engine = GameEngine(600, 650)
                for step in range(100):
                    engine.update()
            actions = {
                330: (0, 0), 342: (0, 1),
                386: (6, 2), 398: (7, 2),
                441: (6, 1), 453: (7, 1),
                496: (1, 1), 508: (1, 2),
            }
            if frame in actions:
                cursor = click(engine, actions[frame])
                cursor_frame = frame
            engine.update()
            engine.render(screen)
            board = engine.board
            special_count = sum(bool(getattr(gem, "special", None))
                                for row in board.grid for gem in row if gem)
            if frame == 325:
                checks[0] = bool(getattr(board, "hint_pair", None))
                observations[0] = "Hint pulses after 5 seconds" if checks[0] else "No hint after 5 seconds"
            if frame == 360:
                checks[1] = board.moves_remaining == original_moves
                observations[1] = f"Invalid swap: {original_moves} -> {board.moves_remaining} moves"
            if frame == 430:
                checks[2] = special_count > 0
                observations[2] = "Four gems create a striped gem" if checks[2] else "Four gems: no special created"
            if frame == 480 and getattr(board, "last_line_clear", None):
                observations[2] = "Striped gem clears the whole row"
            if frame == 585:
                checks[3] = board.score == 90
                observations[3] = f"Two matches: {board.score} points"
            if frame in (325, 360, 430, 480, 585):
                evidence.append({
                    "frame": frame, "time_seconds": frame / 60,
                    "score": board.score, "moves": board.moves_remaining,
                    "special_gems": special_count,
                    "hint": getattr(board, "hint_pair", None),
                    "combo": getattr(board, "combo_multiplier", None),
                    "line_clear": getattr(board, "last_line_clear", None),
                })
            canvas.fill((15, 18, 25))
            canvas.blit(title_font.render(f"{label.upper()}  /  MATCH-3 REPAIR LAB", True, (245, 245, 250)), (20, 10))
            canvas.blit(screen, (0, 45))
            if cursor and frame - cursor_frame < 18:
                pygame.draw.circle(canvas, (255, 255, 255), (cursor[0], cursor[1] + 45), 14, 3)
            titles = ["1  IDLE HINT", "2  INVALID SWAP", "3  SPECIAL GEM", "4  CASCADE COMBO"]
            descriptions = [
                "Wait >5s without input",
                "A rejected swap should cost 0",
                "Match four, then activate it",
                "First match x1, next match x2",
            ]
            for index, title in enumerate(titles):
                top = 90 + index * 130
                color = (90, 225, 175) if checks[index] else (235, 170, 95)
                pygame.draw.rect(canvas, (29, 34, 44), (615, top, 330, 113), border_radius=8)
                if index == active:
                    pygame.draw.rect(canvas, (145, 170, 220), (615, top, 330, 113), 2, border_radius=8)
                canvas.blit(text_font.render(title, True, (240, 242, 250)), (629, top + 14))
                canvas.blit(small_font.render(descriptions[index], True, (174, 184, 202)), (629, top + 43))
                canvas.blit(small_font.render(observations[index], True, color), (629, top + 75))
            canvas.blit(small_font.render("Scripted gameplay / reproducible setups / 60 FPS", True, (170, 180, 195)), (20, 699))
            canvas.blit(small_font.render(f"{frame / 60:04.1f} / 10.0s", True, (170, 180, 195)), (835, 699))
            encoder.stdin.write(pygame.image.tobytes(canvas, "RGB"))
            if frame in (325, 360, 430, 480, 585):
                pygame.image.save(canvas, str(output / f"{label}-{frame}.png"))
    encoder.stdin.close()
    if encoder.wait() != 0:
        raise RuntimeError("Video encoding failed")
    pygame.quit()
    (output / f"{label}-evidence.json").write_text(json.dumps({
        "source_sha256": hashes, "frames": 600, "fps": 60,
        "observations": evidence, "checks": checks,
    }, indent=2) + "\n")
    print(json.dumps({"video": str(output / f"{label}.mp4"), "checks": checks, "observations": evidence}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("label", choices=("before", "after"))
    parser.add_argument("--output", type=Path, default=ROOT / "recordings")
    arguments = parser.parse_args()
    record(arguments.label, arguments.output)
