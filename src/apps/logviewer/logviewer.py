import pygame
import subprocess
import os

BG     = (10, 10, 20)
TEXT   = (255, 255, 255)
ACCENT = (0, 200, 255)
GREEN  = (0, 255, 100)
DIM    = (80, 80,   80)
RED    = (255, 80,  80)
YELLOW = (255, 200,  0)

LOGS = [
    {"name": "Syslog",   "path": "/var/log/syslog"},
    {"name": "Auth",     "path": "/var/log/auth.log"},
    {"name": "Kern",     "path": "/var/log/kern.log"},
    {"name": "Dmesg",    "path": "dmesg"},
    {"name": "Boot",     "path": "/var/log/boot.log"},
    {"name": "Messages", "path": "/var/log/messages"},
]

class LogViewer:
    def __init__(self, screen, font):
        self.screen   = screen
        self.font     = font
        self.mode     = "menu"
        self.selected = 0
        self.lines    = []
        self.scroll   = 0
        self.status   = ""
        self.filter   = ""
        self.filter_mode = False

    def load_log(self, log):
        try:
            if log["path"] == "dmesg":
                result = subprocess.check_output(
                    ["dmesg", "--color=never"],
                    stderr=subprocess.DEVNULL
                ).decode()
                self.lines = result.split("\n")
            else:
                if os.path.exists(log["path"]):
                    with open(log["path"]) as f:
                        self.lines = f.readlines()
                else:
                    self.lines  = [f"File not found: {log['path']}"]
            self.scroll = max(0, len(self.lines) - 12)
            self.status = f"{len(self.lines)} lines"
            self.mode   = "view"
        except Exception as e:
            self.lines  = [f"Error: {e}"]
            self.scroll = 0
            self.mode   = "view"

    def filtered_lines(self):
        if self.filter:
            return [l for l in self.lines if self.filter.lower() in l.lower()]
        return self.lines

    def draw_menu(self):
        self.screen.fill(BG)
        title = self.font.render("Log Viewer", True, ACCENT)
        self.screen.blit(title, (8, 8))
        pygame.draw.line(self.screen, ACCENT, (0, 24), (240, 24), 1)

        y = 32
        for i, log in enumerate(LOGS):
            color = ACCENT if i == self.selected else TEXT
            if i == self.selected:
                pygame.draw.rect(self.screen, (20, 40, 70), (4, y - 1, 232, 15), border_radius=4)
            exists = os.path.exists(log["path"]) or log["path"] == "dmesg"
            ec     = GREEN if exists else RED
            label  = self.font.render(log["name"], True, color)
            path   = self.font.render(log["path"][-20:], True, ec)
            self.screen.blit(label, (8,   y))
            self.screen.blit(path,  (80,  y))
            y += 22

        hint = self.font.render("UP DOWN=select  ENTER=open", True, DIM)
        self.screen.blit(hint, (8, 228))
        pygame.display.flip()

    def draw_view(self):
        self.screen.fill(BG)
        log   = LOGS[self.selected]
        title = self.font.render(log["name"], True, ACCENT)
        self.screen.blit(title, (8, 8))

        if self.filter:
            filt = self.font.render(f"/{self.filter}", True, YELLOW)
            self.screen.blit(filt, (80, 8))

        pygame.draw.line(self.screen, ACCENT, (0, 24), (240, 24), 1)

        lines = self.filtered_lines()
        y     = 28
        for line in lines[self.scroll:self.scroll + 12]:
            stripped = line.strip()[:30]
            color    = RED if "error" in stripped.lower() or "fail" in stripped.lower() else \
                       YELLOW if "warn" in stripped.lower() else TEXT
            surf     = self.font.render(stripped, True, color)
            self.screen.blit(surf, (8, y))
            y += 16

        total = len(lines)
        info  = self.font.render(f"{self.scroll}/{total}", True, DIM)
        self.screen.blit(info, (8, 210))

        hint = self.font.render("UP DOWN  F=filter  ESC=back", True, DIM)
        self.screen.blit(hint, (8, 228))
        pygame.display.flip()

    def draw_filter(self):
        self.screen.fill(BG)
        title = self.font.render("Filter Logs", True, ACCENT)
        self.screen.blit(title, (8, 8))
        pygame.draw.line(self.screen, ACCENT, (0, 24), (240, 24), 1)

        label = self.font.render("Filter keyword:", True, GREEN)
        self.screen.blit(label, (8, 40))
        inp = self.font.render(f"{self.filter}_", True, TEXT)
        self.screen.blit(inp, (8, 58))

        hint = self.font.render("ENTER=apply  ESC=cancel", True, DIM)
        self.screen.blit(hint, (8, 228))
        pygame.display.flip()

    def draw(self):
        if self.mode == "menu":
            self.draw_menu()
        elif self.mode == "view":
            self.draw_view()
        elif self.mode == "filter":
            self.draw_filter()

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if self.mode == "menu":
                if event.key == pygame.K_DOWN:
                    self.selected = min(self.selected + 1, len(LOGS) - 1)
                elif event.key == pygame.K_UP:
                    self.selected = max(self.selected - 1, 0)
                elif event.key == pygame.K_RETURN:
                    self.load_log(LOGS[self.selected])

            elif self.mode == "view":
                lines = self.filtered_lines()
                if event.key == pygame.K_DOWN:
                    self.scroll = min(self.scroll + 1, max(0, len(lines) - 12))
                elif event.key == pygame.K_UP:
                    self.scroll = max(self.scroll - 1, 0)
                elif event.key == pygame.K_f:
                    self.mode   = "filter"
                    self.filter = ""
                elif event.key == pygame.K_ESCAPE:
                    self.mode   = "menu"
                    self.filter = ""
                    self.lines  = []

            elif self.mode == "filter":
                if event.key == pygame.K_RETURN:
                    self.mode   = "view"
                    self.scroll = 0
                elif event.key == pygame.K_BACKSPACE:
                    self.filter = self.filter[:-1]
                elif event.key == pygame.K_ESCAPE:
                    self.mode   = "view"
                else:
                    self.filter += event.unicode
