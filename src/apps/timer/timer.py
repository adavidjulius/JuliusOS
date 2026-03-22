import pygame
import time

BG     = (10, 10, 20)
TEXT   = (255, 255, 255)
ACCENT = (0, 200, 255)
GREEN  = (0, 255, 100)
DIM    = (80, 80,   80)
RED    = (255, 80,  80)
YELLOW = (255, 200,  0)

class Timer:
    def __init__(self, screen, font):
        self.screen     = screen
        self.font       = font
        self.font_big   = pygame.font.SysFont("monospace", 28, bold=True)
        self.mode       = "menu"
        self.sw_running = False
        self.sw_start   = 0
        self.sw_elapsed = 0
        self.sw_laps    = []
        self.tm_input   = ""
        self.tm_seconds = 0
        self.tm_start   = 0
        self.tm_running = False
        self.tm_stage   = "input"

    def fmt_time(self, seconds):
        h   = int(seconds // 3600)
        m   = int((seconds % 3600) // 60)
        s   = int(seconds % 60)
        ms  = int((seconds % 1) * 100)
        if h > 0:
            return f"{h:02d}:{m:02d}:{s:02d}"
        return f"{m:02d}:{s:02d}.{ms:02d}"

    def draw_menu(self):
        self.screen.fill(BG)
        title = self.font.render("Timer & Stopwatch", True, ACCENT)
        self.screen.blit(title, (8, 8))
        pygame.draw.line(self.screen, ACCENT, (0, 24), (240, 24), 1)

        sw = self.font.render("1  Stopwatch", True, TEXT)
        tm = self.font.render("2  Countdown Timer", True, TEXT)
        self.screen.blit(sw, (8, 60))
        self.screen.blit(tm, (8, 90))

        hint = self.font.render("Press 1 or 2", True, DIM)
        self.screen.blit(hint, (8, 228))
        pygame.display.flip()

    def draw_stopwatch(self):
        self.screen.fill(BG)
        title = self.font.render("Stopwatch", True, ACCENT)
        self.screen.blit(title, (8, 8))
        pygame.draw.line(self.screen, ACCENT, (0, 24), (240, 24), 1)

        elapsed = self.sw_elapsed
        if self.sw_running:
            elapsed += time.time() - self.sw_start

        color   = GREEN if self.sw_running else TEXT
        display = self.font_big.render(self.fmt_time(elapsed), True, color)
        self.screen.blit(display, (
            120 - display.get_width() // 2, 50
        ))

        y = 100
        for i, lap in enumerate(self.sw_laps[-6:]):
            lc   = self.font.render(f"Lap {i+1}: {self.fmt_time(lap)}", True, DIM)
            self.screen.blit(lc, (8, y))
            y   += 16

        hint = self.font.render("S=start/stop  L=lap  R=reset", True, DIM)
        self.screen.blit(hint, (8, 228))
        pygame.display.flip()

    def draw_timer_input(self):
        self.screen.fill(BG)
        title = self.font.render("Countdown Timer", True, ACCENT)
        self.screen.blit(title, (8, 8))
        pygame.draw.line(self.screen, ACCENT, (0, 24), (240, 24), 1)

        label = self.font.render("Enter seconds:", True, GREEN)
        self.screen.blit(label, (8, 40))
        inp = self.font.render(f"{self.tm_input}_", True, TEXT)
        self.screen.blit(inp, (8, 58))

        hint = self.font.render("ENTER=start  ESC=back", True, DIM)
        self.screen.blit(hint, (8, 228))
        pygame.display.flip()

    def draw_timer_run(self):
        self.screen.fill(BG)
        title = self.font.render("Countdown", True, ACCENT)
        self.screen.blit(title, (8, 8))
        pygame.draw.line(self.screen, ACCENT, (0, 24), (240, 24), 1)

        elapsed   = time.time() - self.tm_start if self.tm_running else 0
        remaining = max(0, self.tm_seconds - elapsed)

        if remaining <= 0 and self.tm_running:
            self.tm_running = False
            color   = RED
            display = self.font_big.render("DONE!", True, color)
        else:
            pct   = remaining / self.tm_seconds if self.tm_seconds else 0
            color = GREEN if pct > 0.5 else YELLOW if pct > 0.2 else RED
            display = self.font_big.render(self.fmt_time(remaining), True, color)

        self.screen.blit(display, (
            120 - display.get_width() // 2, 50
        ))

        bar_w = int(224 * (remaining / self.tm_seconds if self.tm_seconds else 0))
        pygame.draw.rect(self.screen, DIM,   (8, 96, 224, 8), border_radius=4)
        pygame.draw.rect(self.screen, color, (8, 96, bar_w, 8), border_radius=4)

        hint = self.font.render("S=start/stop  R=reset  ESC=back", True, DIM)
        self.screen.blit(hint, (8, 228))
        pygame.display.flip()

    def draw(self):
        if self.mode == "menu":
            self.draw_menu()
        elif self.mode == "stopwatch":
            self.draw_stopwatch()
        elif self.mode == "timer_input":
            self.draw_timer_input()
        elif self.mode == "timer_run":
            self.draw_timer_run()

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if self.mode == "menu":
                if event.key == pygame.K_1:
                    self.mode = "stopwatch"
                elif event.key == pygame.K_2:
                    self.mode     = "timer_input"
                    self.tm_input = ""

            elif self.mode == "stopwatch":
                if event.key == pygame.K_s:
                    if self.sw_running:
                        self.sw_elapsed += time.time() - self.sw_start
                        self.sw_running  = False
                    else:
                        self.sw_start   = time.time()
                        self.sw_running = True
                elif event.key == pygame.K_l:
                    if self.sw_running:
                        lap = self.sw_elapsed + (time.time() - self.sw_start)
                        self.sw_laps.append(lap)
                elif event.key == pygame.K_r:
                    self.sw_running = False
                    self.sw_elapsed = 0
                    self.sw_laps    = []
                elif event.key == pygame.K_ESCAPE:
                    self.mode = "menu"

            elif self.mode == "timer_input":
                if event.key == pygame.K_RETURN and self.tm_input:
                    self.tm_seconds = int(self.tm_input)
                    self.tm_start   = time.time()
                    self.tm_running = True
                    self.mode       = "timer_run"
                elif event.key == pygame.K_BACKSPACE:
                    self.tm_input = self.tm_input[:-1]
                elif event.key == pygame.K_ESCAPE:
                    self.mode = "menu"
                elif event.unicode.isdigit():
                    self.tm_input += event.unicode

            elif self.mode == "timer_run":
                if event.key == pygame.K_s:
                    if self.tm_running:
                        self.tm_running = False
                    else:
                        self.tm_start   = time.time()
                        self.tm_running = True
                elif event.key == pygame.K_r:
                    self.tm_running = False
                    self.tm_start   = 0
                    self.mode       = "timer_input"
                    self.tm_input   = ""
                elif event.key == pygame.K_ESCAPE:
                    self.tm_running = False
                    self.mode       = "menu"
