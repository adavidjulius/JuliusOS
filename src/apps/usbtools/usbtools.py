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

class USBTools:
    def __init__(self, screen, font):
        self.screen   = screen
        self.font     = font
        self.devices  = []
        self.selected = 0
        self.scroll   = 0
        self.status   = "Press S to scan USB"
        self.mode     = "list"
        self.details  = []

    def scan(self):
        try:
            result = subprocess.check_output(
                ["lsusb"], stderr=subprocess.DEVNULL
            ).decode()
            self.devices = []
            for line in result.strip().split("\n"):
                parts = line.split("ID ")
                if len(parts) >= 2:
                    rest = parts[1].split(" ", 1)
                    self.devices.append({
                        "id"  : rest[0] if rest else "?",
                        "name": rest[1][:24] if len(rest) > 1 else "Unknown",
                        "raw" : line
                    })
            self.status = f"{len(self.devices)} USB devices"
        except Exception as e:
            self.status  = f"Error: {e}"
            self.devices = []

    def get_details(self, device):
        try:
            vid, pid = device["id"].split(":")
            result   = subprocess.check_output(
                ["lsusb", "-d", device["id"], "-v"],
                stderr=subprocess.DEVNULL
            ).decode()
            self.details = [l.strip()[:30] for l in result.split("\n") if l.strip()][:20]
            self.mode    = "detail"
        except Exception as e:
            self.details = [f"Error: {e}"]
            self.mode    = "detail"

    def get_mounted(self):
        try:
            result = subprocess.check_output(
                ["lsblk", "-o", "NAME,SIZE,MOUNTPOINT,TYPE"],
                stderr=subprocess.DEVNULL
            ).decode()
            self.details = [l.strip()[:30] for l in result.split("\n") if l.strip()]
            self.mode    = "detail"
        except Exception as e:
            self.details = [f"Error: {e}"]
            self.mode    = "detail"

    def draw_list(self):
        self.screen.fill(BG)
        title = self.font.render("USB Tools", True, ACCENT)
        self.screen.blit(title, (8, 8))
        pygame.draw.line(self.screen, ACCENT, (0, 24), (240, 24), 1)

        color  = GREEN if "devices" in self.status else RED
        status = self.font.render(self.status[:30], True, color)
        self.screen.blit(status, (8, 27))
        pygame.draw.line(self.screen, DIM, (0, 38), (240, 38), 1)

        if not self.devices:
            msg = self.font.render("Press S to scan", True, DIM)
            self.screen.blit(msg, (8, 100))
        else:
            y = 42
            for i, dev in enumerate(self.devices[self.scroll:self.scroll + 8]):
                idx   = i + self.scroll
                color = ACCENT if idx == self.selected else TEXT
                if idx == self.selected:
                    pygame.draw.rect(self.screen, (20, 40, 70), (4, y - 1, 232, 26), border_radius=3)
                uid  = self.font.render(dev["id"],   True, DIM)
                name = self.font.render(dev["name"], True, color)
                self.screen.blit(uid,  (8, y))
                self.screen.blit(name, (8, y + 13))
                y += 30

        hint = self.font.render("S=scan  ENTER=detail  M=mounts", True, DIM)
        self.screen.blit(hint, (8, 228))
        pygame.display.flip()

    def draw_detail(self):
        self.screen.fill(BG)
        title = self.font.render("USB Detail", True, ACCENT)
        self.screen.blit(title, (8, 8))
        pygame.draw.line(self.screen, ACCENT, (0, 24), (240, 24), 1)

        y = 30
        for line in self.details[:12]:
            surf = self.font.render(line[:30], True, TEXT)
            self.screen.blit(surf, (8, y))
            y += 16

        hint = self.font.render("ESC=back", True, DIM)
        self.screen.blit(hint, (8, 228))
        pygame.display.flip()

    def draw(self):
        if self.mode == "list":
            self.draw_list()
        elif self.mode == "detail":
            self.draw_detail()

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if self.mode == "list":
                if event.key == pygame.K_DOWN:
                    if self.selected < len(self.devices) - 1:
                        self.selected += 1
                    if self.selected >= self.scroll + 8:
                        self.scroll += 1
                elif event.key == pygame.K_UP:
                    if self.selected > 0:
                        self.selected -= 1
                    if self.selected < self.scroll:
                        self.scroll -= 1
                elif event.key == pygame.K_s:
                    self.scan()
                elif event.key == pygame.K_RETURN:
                    if self.devices:
                        self.get_details(self.devices[self.selected])
                elif event.key == pygame.K_m:
                    self.get_mounted()
            elif self.mode == "detail":
                if event.key == pygame.K_ESCAPE:
                    self.mode = "list"
