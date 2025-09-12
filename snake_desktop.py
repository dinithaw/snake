"""
Cross-platform Snake game (Windows / macOS / Linux)
Single-file Python game using Pygame.
Features:
 - Keyboard controls (Arrow keys, WASD)
 - Mouse/touch swipe support (basic)
 - Settings overlay: choose colors (presets), toggle wrap/walls, grid size, speed
 - Save/load settings to local JSON (in same folder)
 - Score / best score persistence

Requirements:
  pip install pygame

Run:
  python snake_desktop.py

To create standalone executables (optional):
  pyinstaller --onefile --windowed snake_desktop.py

"""
import sys
import os
import json
import math
import pygame
from pygame import gfxdraw

# -----------------------
# Configuration / Defaults
# -----------------------
APP_NAME = "Snake - Desktop"
SETTINGS_FILE = "snake_settings.json"
BEST_FILE = "snake_best.json"

DEFAULT = {
    "grid": 20,
    "cell_size": 24,
    "speed": 8.0,            # moves per second
    "wrap": True,
    "colors": {
        "grid_a": "#121633",
        "grid_b": "#10122b",
        "snake_head": "#8fff8f",
        "snake_body": "#56d856",
        "food": "#6ee7ff",
        "bg": "#0f1226"
    }
}

PRESET_PALETTES = [
    {"name": "Classic", "colors": DEFAULT["colors"]},
    {"name": "Sunset", "colors": {"grid_a":"#2b1120","grid_b":"#321a2b","snake_head":"#ffd166","snake_body":"#ff8a5b","food":"#ff6b6b","bg":"#1b0510"}},
    {"name": "Ocean", "colors": {"grid_a":"#052d3a","grid_b":"#063845","snake_head":"#00ffd5","snake_body":"#00c2a8","food":"#ffd800","bg":"#001f2d"}},
    {"name": "Monochrome", "colors": {"grid_a":"#1b1b1b","grid_b":"#111111","snake_head":"#ffffff","snake_body":"#cfcfcf","food":"#9f9f9f","bg":"#000000"}},
]

# -----------------------
# Utility helpers
# -----------------------

def hex_to_rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def clamp(v, a, b):
    return max(a, min(b, v))


# -----------------------
# Settings persistence
# -----------------------

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    return DEFAULT.copy()


def save_settings(s):
    try:
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(s, f, indent=2)
    except Exception as e:
        print("Warning: failed to save settings:", e)


def load_best():
    if os.path.exists(BEST_FILE):
        try:
            with open(BEST_FILE, 'r') as f:
                return json.load(f).get('best', 0)
        except Exception:
            pass
    return 0


def save_best(b):
    try:
        with open(BEST_FILE, 'w') as f:
            json.dump({'best': b}, f)
    except Exception as e:
        print("Warning: failed to save best:", e)


# -----------------------
# Game classes
# -----------------------

class Game:
    def __init__(self, settings):
        pygame.init()
        pygame.display.set_caption(APP_NAME)

        self.settings = settings
        self.grid = settings.get('grid', DEFAULT['grid'])
        self.cell = settings.get('cell_size', DEFAULT['cell_size'])
        self.speed = settings.get('speed', DEFAULT['speed'])
        self.wrap = settings.get('wrap', True)
        self.colors = settings.get('colors', DEFAULT['colors'])

        # compute window size
        self.board_px = self.grid * self.cell
        w = self.board_px + 240  # side panel for settings
        h = max(self.board_px, 520)
        self.screen = pygame.display.set_mode((w, h), pygame.RESIZABLE)
        self.clock = pygame.time.Clock()

        # game state
        self.reset()
        self.best = load_best()
        self.running = True
        self.paused = False

        # input tracking for swipe (mouse/touch)
        self.swipe_start = None
        self.SWIPE_THRESHOLD = max(16, self.cell//2)

        # UI state
        self.show_settings = False
        self.selected_palette = 0

    def reset(self):
        mid = self.grid // 2
        start_len = 4
        self.snake = [(mid - i, mid) for i in range(start_len)]
        self.dir = (1, 0)
        self.next_dir = self.dir
        self.spawn_food()
        self.score = 0
        self.ticks = 0
        self.tick_timer = 0.0  # seconds accumulator

    def spawn_food(self):
        import random
        while True:
            f = (random.randrange(self.grid), random.randrange(self.grid))
            if f not in self.snake:
                self.food = f
                return

    def update(self, dt):
        if not self.running or self.paused or self.show_settings:
            return
        self.tick_timer += dt
        step = 1.0 / self.speed
        while self.tick_timer >= step:
            self.tick()
            self.tick_timer -= step

    def tick(self):
        self.dir = self.next_dir
        hx, hy = self.snake[0]
        nx = hx + self.dir[0]
        ny = hy + self.dir[1]
        if self.wrap:
            nx %= self.grid
            ny %= self.grid
        else:
            if nx < 0 or nx >= self.grid or ny < 0 or ny >= self.grid:
                self.game_over()
                return
        if (nx, ny) in self.snake:
            self.game_over(); return
        self.snake.insert(0, (nx, ny))
        if (nx, ny) == self.food:
            self.score += 1
            self.speed = clamp(self.speed + 0.4, 3.0, 24.0)
            self.spawn_food()
        else:
            self.snake.pop()

    def game_over(self):
        self.running = False
        if self.score > self.best:
            self.best = self.score
            save_best(self.best)

    def draw(self):
        self.screen.fill(hex_to_rgb(self.colors.get('bg', '#000000')))
        # draw board background centered
        sx = 20
        sy = 20
        board_rect = pygame.Rect(sx, sy, self.board_px, self.board_px)
        # grid
        grd_a = hex_to_rgb(self.colors.get('grid_a', '#121633'))
        grd_b = hex_to_rgb(self.colors.get('grid_b', '#10122b'))
        for y in range(self.grid):
            for x in range(self.grid):
                r = pygame.Rect(sx + x*self.cell, sy + y*self.cell, self.cell-1, self.cell-1)
                color = grd_a if ((x+y)&1) else grd_b
                pygame.draw.rect(self.screen, color, r)
        # food
        fx, fy = self.food
        fcolor = hex_to_rgb(self.colors.get('food', '#6ee7ff'))
        fr = pygame.Rect(sx + fx*self.cell + 4, sy + fy*self.cell + 4, self.cell-8, self.cell-8)
        pygame.draw.ellipse(self.screen, fcolor, fr)
        # snake
        head_color = hex_to_rgb(self.colors.get('snake_head', '#8fff8f'))
        body_color = hex_to_rgb(self.colors.get('snake_body', '#56d856'))
        for i, (x, y) in enumerate(self.snake):
            rect = pygame.Rect(sx + x*self.cell + 2, sy + y*self.cell + 2, self.cell-4, self.cell-4)
            pygame.draw.rect(self.screen, body_color if i>0 else head_color, rect, border_radius=6)
        # side panel
        panel_x = sx + self.board_px + 16
        self.draw_ui(panel_x, sy)

    def draw_ui(self, x, sy):
        # background panel
        panel_w = self.screen.get_width() - x - 20
        panel_h = self.board_px
        panel_rect = pygame.Rect(x, sy, panel_w, panel_h)
        pygame.draw.rect(self.screen, (20, 22, 40), panel_rect, border_radius=8)
        font = pygame.font.SysFont(None, 20)
        big = pygame.font.SysFont(None, 26, bold=True)
        # title
        t = big.render(APP_NAME, True, (230,230,240))
        self.screen.blit(t, (x+14, sy+12))
        # score
        s = font.render(f"Score: {self.score}", True, (220,220,220))
        self.screen.blit(s, (x+14, sy+50))
        b = font.render(f"Best: {self.best}", True, (200,200,200))
        self.screen.blit(b, (x+14, sy+76))
        sp = font.render(f"Speed: {self.speed:.2f}", True, (200,200,200))
        self.screen.blit(sp, (x+14, sy+100))
        gs = font.render(f"Grid: {self.grid}x{self.grid}", True, (200,200,200))
        self.screen.blit(gs, (x+14, sy+124))
        wr = font.render(f"Wrap: {'On' if self.wrap else 'Off'}", True, (200,200,200))
        self.screen.blit(wr, (x+14, sy+148))

        # buttons: Show settings hint
        hint = font.render("Press S to open Settings", True, (190,190,200))
        self.screen.blit(hint, (x+14, sy+panel_h-36))

        # draw settings overlay if active
        if self.show_settings:
            self.draw_settings_overlay()

    def draw_settings_overlay(self):
        w, h = self.screen.get_size()
        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        overlay.fill((0,0,0,160))
        # panel
        pw = min(520, w-80)
        ph = min(640, h-120)
        px = (w - pw)//2
        py = (h - ph)//2
        pygame.draw.rect(overlay, (26,28,48,240), (px,py,pw,ph), border_radius=10)
        # draw content
        font = pygame.font.SysFont(None, 20)
        big = pygame.font.SysFont(None, 28, bold=True)
        overlay.blit(big.render('Settings', True, (240,240,240)), (px+18, py+16))
        # presets
        overlay.blit(font.render('Palettes:', True, (220,220,220)), (px+18, py+58))
        yy = py+84
        for i, p in enumerate(PRESET_PALETTES):
            rect = pygame.Rect(px+18 + i*110, yy, 96, 48)
            pygame.draw.rect(overlay, (40,42,60,230), rect, border_radius=6)
            # draw small palette preview
            c = p['colors']
            pygame.draw.rect(overlay, hex_to_rgb(c['grid_a'])+(255,), (rect.x+6, rect.y+6, 22, 36))
            pygame.draw.rect(overlay, hex_to_rgb(c['grid_b'])+(255,), (rect.x+34, rect.y+6, 22, 36))
            pygame.draw.rect(overlay, hex_to_rgb(c['snake_head'])+(255,), (rect.x+62, rect.y+6, 14, 16))
            pygame.draw.rect(overlay, hex_to_rgb(c['snake_body'])+(255,), (rect.x+62, rect.y+26, 14, 16))
            name = font.render(p['name'], True, (220,220,220))
            overlay.blit(name, (rect.x+6, rect.y+44-8))
            # mark selected
            if i == self.selected_palette:
                pygame.draw.rect(overlay, (255,255,255,200), rect, width=2, border_radius=6)
        yy += 72
        # toggles and sliders (simple render)
        overlay.blit(font.render('Grid size: (left/right)  -  current: ' + str(self.grid), True, (220,220,220)), (px+18, yy))
        yy += 28
        overlay.blit(font.render('Speed: (up/down) - current: ' + f"{self.speed:.2f}", True, (220,220,220)), (px+18, yy))
        yy += 28
        overlay.blit(font.render('Wrap (W) - current: ' + ('On' if self.wrap else 'Off'), True, (220,220,220)), (px+18, yy))
        yy += 40
        overlay.blit(font.render('Presets: press number keys 1-' + str(len(PRESET_PALETTES)), True, (200,200,200)), (px+18, yy))
        yy += 28
        overlay.blit(font.render('Save (Ctrl+S)  •  Close (Esc/S)', True, (200,200,200)), (px+18, yy))

        self.screen.blit(overlay, (0,0))

    # --- Input handling ---
    def handle_event(self, e):
        if e.type == pygame.QUIT:
            self.running = False
            pygame.quit(); sys.exit()
        elif e.type == pygame.VIDEORESIZE:
            self.screen = pygame.display.set_mode((e.w, e.h), pygame.RESIZABLE)
        elif e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_UP, pygame.K_w): self.try_set_dir(0, -1)
            elif e.key in (pygame.K_DOWN, pygame.K_s): self.try_set_dir(0, 1)
            elif e.key in (pygame.K_LEFT, pygame.K_a): self.try_set_dir(-1, 0)
            elif e.key in (pygame.K_RIGHT, pygame.K_d): self.try_set_dir(1, 0)
            elif e.key == pygame.K_SPACE: self.paused = not self.paused
            elif e.key == pygame.K_s:
                self.show_settings = not self.show_settings
            elif e.key == pygame.K_w:
                # toggle wrap (but we used w for up also - only when settings open)
                if self.show_settings:
                    self.wrap = not self.wrap
            elif e.key == pygame.K_ESCAPE:
                if self.show_settings:
                    self.show_settings = False
            elif self.show_settings:
                if pygame.K_1 <= e.key <= pygame.K_9:
                    idx = e.key - pygame.K_1
                    if idx < len(PRESET_PALETTES):
                        self.apply_palette(idx)
                elif e.key == pygame.K_UP:
                    self.speed = clamp(self.speed + 0.5, 1.0, 24.0)
                elif e.key == pygame.K_DOWN:
                    self.speed = clamp(self.speed - 0.5, 1.0, 24.0)
                elif e.key == pygame.K_LEFT:
                    self.grid = clamp(self.grid - 2, 8, 48)
                    self.rebuild_board()
                elif e.key == pygame.K_RIGHT:
                    self.grid = clamp(self.grid + 2, 8, 48)
                    self.rebuild_board()
                elif (e.mod & pygame.KMOD_CTRL) and e.key == pygame.K_s:
                    # save settings
                    self.settings['grid'] = self.grid
                    self.settings['cell_size'] = self.cell
                    self.settings['speed'] = self.speed
                    self.settings['wrap'] = self.wrap
                    self.settings['colors'] = self.colors
                    save_settings(self.settings)
            else:
                # regular keys when not settings
                pass
        elif e.type == pygame.MOUSEBUTTONDOWN:
            if e.button == 1:
                self.swipe_start = e.pos
        elif e.type == pygame.MOUSEBUTTONUP:
            if e.button == 1 and self.swipe_start:
                sx, sy = self.swipe_start
                ex, ey = e.pos
                dx = ex - sx; dy = ey - sy
                if abs(dx) > abs(dy) and abs(dx) > self.SWIPE_THRESHOLD:
                    self.try_set_dir(1 if dx>0 else -1, 0)
                elif abs(dy) > self.SWIPE_THRESHOLD:
                    self.try_set_dir(0, 1 if dy>0 else -1)
                self.swipe_start = None
        elif e.type == pygame.FINGERDOWN:
            # touch start
            self.swipe_start = (int(e.x * self.screen.get_width()), int(e.y * self.screen.get_height()))
        elif e.type == pygame.FINGERUP:
            if self.swipe_start:
                sx, sy = self.swipe_start
                ex = int(e.x * self.screen.get_width())
                ey = int(e.y * self.screen.get_height())
                dx = ex - sx; dy = ey - sy
                if abs(dx) > abs(dy) and abs(dx) > self.SWIPE_THRESHOLD:
                    self.try_set_dir(1 if dx>0 else -1, 0)
                elif abs(dy) > self.SWIPE_THRESHOLD:
                    self.try_set_dir(0, 1 if dy>0 else -1)
                self.swipe_start = None

    def try_set_dir(self, x, y):
        # prevent reversing
        if (x == -self.dir[0] and y == -self.dir[1]): return
        self.next_dir = (x, y)

    def apply_palette(self, idx):
        p = PRESET_PALETTES[idx]['colors']
        self.colors.update(p)
        self.selected_palette = idx

    def rebuild_board(self):
        # rebuild pixel sizes
        self.cell = max(8, int(self.cell))
        self.board_px = self.grid * self.cell
        w = self.board_px + 240
        h = max(self.board_px, 520)
        self.screen = pygame.display.set_mode((w, h), pygame.RESIZABLE)

    def run(self):
        font = pygame.font.SysFont(None, 24)
        last_time = pygame.time.get_ticks() / 1000.0
        while True:
            now = pygame.time.get_ticks() / 1000.0
            dt = now - last_time
            last_time = now
            for e in pygame.event.get():
                self.handle_event(e)
            if not self.running:
                # show game over prompt - restart on Enter
                keys = pygame.key.get_pressed()
                if keys[pygame.K_RETURN] or keys[pygame.K_r]:
                    self.running = True
                    self.reset()
            self.update(dt)
            self.draw()
            pygame.display.flip()
            self.clock.tick(60)


# -----------------------
# Main entry
# -----------------------

def main():
    try:
        settings = load_settings()
        game = Game(settings)
        game.run()
    except Exception as e:
        print("An error occurred:", e)
        pygame.quit()


if __name__ == '__main__':
    main()
