import pygame
import json
import os

BG     = (10, 10, 20)
TEXT   = (255, 255, 255)
ACCENT = (150, 150, 150)
ON_COL = (0, 255, 100)

SETTINGS_FILE = "julius_settings.json"

DEFAULT = {
    "brightness": 100,
    "wifi"      : True,
    "bluetooth" : True,
    "version"   : "Julius OS v0.1",
    "device"    : "Julius Gadget"
}

class Settings:
    def __init__(self, screen, font):
        self.screen   = screen
        self.font     = font
        self.config   = self.load()
        self.selected = 0
        self.items    = list(self.config.items())

    def load(self):
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE) as f:
                return json.load(f)
        return DEFAULT.copy()

    def save(self):
        with open(SETTINGS_FILE, "w") as f:
            json.dump(self.config, f)

    def draw(self):
        self.screen.fill(BG)
        title = self.font.render("Settings", True, ACCENT)
        self.screen.blit(title, (8, 8))
        pygame.draw.line(self.screen, ACCENT, (0, 24), (240, 24), 1)
        self.items = list(self.config.items())
        y = 32
        for i, (key, val) in enumerate(self.items):
            color   = ON_COL if i == self.selected else TEXT
            display = f"{key:<12} {'ON' if val else 'OFF'}" if isinstance(val, bool) else f"{key:<12} {val}"
            label   = self.font.render(display, True, color)
            self.screen.blit(label, (8, y))
            y += 18
        self.screen.blit(hint, (8, 225))
        pygame.display.flip()

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_DOWN:
                self.selected = (self.selected + 1) % len(self.items)
            elif event.key == pygame.K_UP:
                self.selected = (self.selected - 1) % len(self.items)
            elif event.key == pygame.K_RETURN:
                key, val = self.items[self.selected]
                if isinstance(val, bool):
                    self.config[key] = not val
                    self.save()
