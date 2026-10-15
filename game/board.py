import math
import random
import pygame

GRID_SIZE = 8
TILE_SIZE = 60
GEM_COLORS = [
    (220, 50, 50),   # Red
    (50, 200, 50),   # Green
    (50, 100, 240),  # Blue
    (240, 200, 40),  # Yellow
    (180, 50, 220),  # Purple
    (240, 130, 40),  # Orange
]


class Gem:
   
    def __init__(self, color, target_row, col):
        self.color = color
        self.target_row = target_row
        self.col = col
        self.current_y = (target_row - 2) * TILE_SIZE
        self.target_y = target_row * TILE_SIZE
        self.fall_speed = 12.0
        self.special = None

    def update(self):
        if self.current_y < self.target_y:
            self.current_y += self.fall_speed
            if self.current_y > self.target_y:
                self.current_y = self.target_y

    def is_animating(self):
        return self.current_y < self.target_y


class Board:

    def __init__(self, offset_x, offset_y, target_score=500, max_moves=20):
        self.offset_x = offset_x
        self.offset_y = offset_y
        self.target_score = target_score
        self.max_moves = max_moves
        self.grid = [[None for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.selected = None
        self.score = 0
        self.moves_remaining = max_moves
        self.reset()

    def reset(self):
        self.score = 0
        self.moves_remaining = self.max_moves
        self.selected = None
        self.combo_multiplier = 0
        self.last_points = 0
        self.resolving = False
        self.last_line_clear = None
        self.clear_flash = set()
        self.flash_until = 0
        self.note_input()
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                color = random.choice(GEM_COLORS)
                gem = Gem(color, r, c)
                gem.current_y = gem.target_y  
                self.grid[r][c] = gem

        self.resolve_matches()

    def is_animating(self):
        return self.resolving or self.gems_are_falling()

    def gems_are_falling(self):
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                if self.grid[r][c] and self.grid[r][c].is_animating():
                    return True
        return False

    def swap_gems(self, pos1, pos2):
        r1, c1 = pos1
        r2, c2 = pos2

        g1, g2 = self.grid[r1][c1], self.grid[r2][c2]
        self.grid[r1][c1], self.grid[r2][c2] = g2, g1

        if self.grid[r1][c1]:
            self.grid[r1][c1].col = c1
            self.grid[r1][c1].target_row = r1
            self.grid[r1][c1].target_y = r1 * TILE_SIZE
            self.grid[r1][c1].current_y = r1 * TILE_SIZE

        if self.grid[r2][c2]:
            self.grid[r2][c2].col = c2
            self.grid[r2][c2].target_row = r2
            self.grid[r2][c2].target_y = r2 * TILE_SIZE
            self.grid[r2][c2].current_y = r2 * TILE_SIZE

    def is_adjacent(self, pos1, pos2):
        r1, c1 = pos1
        r2, c2 = pos2
        return abs(r1 - r2) + abs(c1 - c2) == 1

    def find_matches(self):
        matched = set()

        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE - 2):
                if (
                    self.grid[r][c]
                    and self.grid[r][c + 1]
                    and self.grid[r][c + 2]
                    and self.grid[r][c].color == self.grid[r][c + 1].color == self.grid[r][c + 2].color
                ):
                    matched.update([(r, c), (r, c + 1), (r, c + 2)])

        for r in range(GRID_SIZE - 2):
            for c in range(GRID_SIZE):
                if (
                    self.grid[r][c]
                    and self.grid[r + 1][c]
                    and self.grid[r + 2][c]
                    and self.grid[r][c].color == self.grid[r + 1][c].color == self.grid[r + 2][c].color
                ):
                    matched.update([(r, c), (r + 1, c), (r + 2, c)])

        return matched

    def matching_runs(self):
        runs = []
        for direction in ("row", "column"):
            for line in range(GRID_SIZE):
                run = []
                previous_color = None
                for offset in range(GRID_SIZE):
                    position = (line, offset) if direction == "row" else (offset, line)
                    row, col = position
                    gem = self.grid[row][col]
                    color = gem.color if gem else None
                    if color is None or color != previous_color:
                        if len(run) >= 3:
                            runs.append((direction, run))
                        run = []
                    if gem:
                        run.append(position)
                    previous_color = color
                if len(run) >= 3:
                    runs.append((direction, run))
        return runs

    def note_input(self):
        self.last_input_time = pygame.time.get_ticks()
        self.hint_pair = None
        self.hint_checked = False

    def find_valid_swap(self):
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                first = (row, col)
                for second in ((row, col + 1), (row + 1, col)):
                    next_row, next_col = second
                    if next_row >= GRID_SIZE or next_col >= GRID_SIZE:
                        continue
                    self.grid[row][col], self.grid[next_row][next_col] = (
                        self.grid[next_row][next_col], self.grid[row][col]
                    )
                    try:
                        matches = self.find_matches()
                    finally:
                        self.grid[row][col], self.grid[next_row][next_col] = (
                            self.grid[next_row][next_col], self.grid[row][col]
                        )
                    if matches:
                        return first, second
        return None

    def clear_matches(self, preferred=()):
        runs = self.matching_runs()
        cleared = {position for direction, run in runs for position in run}
        pending = list(cleared)
        activated = set()
        blast = set()
        while pending:
            row, col = pending.pop()
            gem = self.grid[row][col]
            if not gem or not gem.special or (row, col) in activated:
                continue
            activated.add((row, col))
            line = {(row, offset) if gem.special == "row" else (offset, col)
                    for offset in range(GRID_SIZE)}
            pending.extend(line - cleared)
            cleared.update(line)
            blast.update(line)

        created = set()
        for direction, run in runs:
            if len(run) < 4 or any(self.grid[row][col].special for row, col in run):
                continue
            candidates = list(preferred) + [run[len(run) // 2]] + run
            anchor = next((position for position in candidates
                           if position in run and position not in blast
                           and position not in created), None)
            if anchor is not None:
                row, col = anchor
                self.grid[row][col].special = direction
                created.add(anchor)

        cleared.difference_update(created)
        self.last_points = len(cleared) * 10 * self.combo_multiplier
        self.score += self.last_points
        self.clear_flash = cleared
        self.flash_until = pygame.time.get_ticks() + 250
        if blast:
            self.last_line_clear = sorted(blast)
        for row, col in cleared:
            self.grid[row][col] = None
        self.drop_and_refill()

    def drop_and_refill(self):
        for c in range(GRID_SIZE):
            empty_slots = 0
            for r in range(GRID_SIZE - 1, -1, -1):
                if self.grid[r][c] is None:
                    empty_slots += 1
                elif empty_slots > 0:
                    gem = self.grid[r][c]
                    gem.target_row = r + empty_slots
                    gem.target_y = (r + empty_slots) * TILE_SIZE
                    self.grid[r + empty_slots][c] = gem
                    self.grid[r][c] = None

            for r in range(empty_slots):
                color = random.choice(GEM_COLORS)
                gem = Gem(color, r, c)
                gem.current_y = -((empty_slots - r) * TILE_SIZE)
                self.grid[r][c] = gem

    def resolve_matches(self):
        total_cleared = 0
        while True:
            matches = self.find_matches()
            if not matches:
                break
            total_cleared += len(matches)
            for r, c in matches:
                self.grid[r][c] = None
            self.drop_and_refill()
        return total_cleared

    def process_swap(self, pos1, pos2):
        self.note_input()
        if not self.is_adjacent(pos1, pos2) or self.is_game_over() or self.is_animating():
            return False

        self.swap_gems(pos1, pos2)
        matches = self.find_matches()

        if not matches:
            self.swap_gems(pos1, pos2)
            return False

        self.moves_remaining -= 1
        self.combo_multiplier = 1
        self.last_line_clear = None
        self.resolving = True
        self.clear_matches(preferred=(pos2, pos1))
        return True

    def is_game_over(self):
        return self.check_result() is not None

    def check_result(self):
        if self.is_animating():
            return None
        if self.score >= self.target_score:
            return "WIN"
        if self.moves_remaining <= 0:
            return "LOSS"
        return None

    def update(self):
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                if self.grid[r][c]:
                    self.grid[r][c].update()

        if self.gems_are_falling():
            return
        if self.resolving:
            if self.find_matches():
                self.combo_multiplier += 1
                self.clear_matches()
            else:
                self.resolving = False
                self.note_input()
            return
        if (not self.is_game_over() and not self.hint_checked
                and pygame.time.get_ticks() - self.last_input_time > 5000):
            self.hint_pair = self.find_valid_swap()
            self.hint_checked = True

    def render(self, surface):
        board_rect = pygame.Rect(
            self.offset_x, self.offset_y, GRID_SIZE * TILE_SIZE, GRID_SIZE * TILE_SIZE
        )
        pygame.draw.rect(surface, (20, 22, 28), board_rect, border_radius=8)
        pygame.draw.rect(surface, (60, 65, 75), board_rect, width=3, border_radius=8)

        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                gem = self.grid[r][c]
                if gem:
                    x = self.offset_x + c * TILE_SIZE
                    y = self.offset_y + gem.current_y
                    tile_rect = pygame.Rect(x + 2, y + 2, TILE_SIZE - 4, TILE_SIZE - 4)

                    pygame.draw.rect(surface, gem.color, tile_rect, border_radius=10)
                    pygame.draw.rect(
                        surface, (255, 255, 255), tile_rect, width=1, border_radius=10
                    )

                    if gem.special:
                        glow = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
                        alpha = int(90 + 45 * math.sin(pygame.time.get_ticks() / 240))
                        pygame.draw.rect(glow, (255, 245, 170, alpha), glow.get_rect(), 5, border_radius=12)
                        surface.blit(glow, (x, y))
                        for stripe in (-6, 6):
                            if gem.special == "row":
                                start = (x + 12, y + TILE_SIZE // 2 + stripe)
                                end = (x + TILE_SIZE - 12, start[1])
                            else:
                                start = (x + TILE_SIZE // 2 + stripe, y + 12)
                                end = (start[0], y + TILE_SIZE - 12)
                            pygame.draw.line(surface, (255, 255, 235), start, end, 4)

                if self.selected == (r, c):
                    sel_x = self.offset_x + c * TILE_SIZE
                    sel_y = self.offset_y + r * TILE_SIZE
                    sel_rect = pygame.Rect(sel_x + 2, sel_y + 2, TILE_SIZE - 4, TILE_SIZE - 4)
                    pygame.draw.rect(
                        surface, (255, 255, 255), sel_rect, width=4, border_radius=10
                    )

        now = pygame.time.get_ticks()
        if now < self.flash_until:
            flash = pygame.Surface((TILE_SIZE - 4, TILE_SIZE - 4), pygame.SRCALPHA)
            flash.fill((255, 255, 220, int(130 * (self.flash_until - now) / 250)))
            for row, col in self.clear_flash:
                surface.blit(flash, (self.offset_x + col * TILE_SIZE + 2,
                                     self.offset_y + row * TILE_SIZE + 2))
        if self.hint_pair and not self.is_animating() and not self.is_game_over():
            brightness = int(190 + 65 * math.sin(now / 220))
            for row, col in self.hint_pair:
                hint_rect = pygame.Rect(self.offset_x + col * TILE_SIZE + 5,
                                       self.offset_y + row * TILE_SIZE + 5,
                                       TILE_SIZE - 10, TILE_SIZE - 10)
                pygame.draw.rect(surface, (brightness, brightness, 150), hint_rect, 4, border_radius=8)
