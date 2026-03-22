import pygame
import socket
import json
import os

BG     = (10, 10, 20)
TEXT   = (255, 255, 255)
ACCENT = (0, 200, 255)
GREEN  = (0, 255, 100)
DIM    = (80, 80,   80)
RED    = (255, 80,  80)

WOL_FILE = "julius_wol.json"

class WakeOnLAN:
    def __init__(self, screen, font):
        self.screen   = screen
        self.font     = font
        self.devices  = self.load()
        self.selected = 0
        self.mode     = "list"
        self.input    = ""
        self.name_in  = ""
        self.mac_in   = ""
        self.stage    = "name"
        self.status   = ""

    def load(self):
        if os.path.exists(WOL_FILE):
            with open(WOL_FILE) as f:
                return json.load(f)
        return []

    def save(self):
        with open(WOL_FILE, "w") as f:
            json.dump(self.devices, f)

    def send_magic(self, mac):
        try:
            mac   = mac.replace(":", "").replace("-", "")
            magic = bytes.fromhex("FF" * 6 + mac * 16)
            s     = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            s.sendto(magic, ("<broadcast>", 9))
            s.close()
            self.status = f"Magic packet sent!"
        except Exception as e:
            self.status = f"Error: {e}"

    def draw_list(self):
        self.screen.fill(BG)
        title = self.font.render("Wake on LAN", True, ACCENT)
        self.screen.blit(title, (8, 8))
        pygame.draw.line(self.screen, ACCENT, (0, 24), (240, 24), 1)

        if self.status:
            st = self.font.render(self.status, True, GREEN)
            self.screen.blit(st, (8, 27))

        pygame.draw.line(self.screen, DIM, (0, 38), (240, 38), 1)

        if not self.devices:
            msg = self.font.render("No devices. Press N to add", True, DIM)
            self.screen.blit(msg, (8, 120))
        else:
            y = 42
            for i, dev in enumerate(self.devices[:10]):
                color = ACCENT if i == self.selected else TEXT
                if i == self.selected:
                    pygame.draw.rect(self.screen, (20, 40, 70), (4, y - 1, 232, 28), border_radius=4)
                name = self.font.render(dev["name"][:20], True, color)
                mac  = self.font.render(dev["mac"],       True, DIM)
                self.screen.blit(name, (8, y))
                self.screen.blit(mac,  (8, y + 13))
                y += 32

        hint = self.font.render("ENTER=wake  N=add  D=del", True, DIM)
        self.screen.blit(hint, (8, 228))
        pygame.display.flip()

    def draw_add(self):
        self.screen.fill(BG)
        title = self.font.render("Add Device", True, ACCENT)
        self.screen.blit(title, (8, 8))
        pygame.draw.line(self.screen, ACCENT, (0, 24), (240, 24), 1)

        if self.stage == "name":
            label = self.font.render("Device Name:", True, GREEN)
            self.screen.blit(label, (8, 40))
            inp = self.font.render(f"{self.name_in}_", True, TEXT)
            self.screen.blit(inp, (8, 60))
        elif self.stage == "mac":
            label = self.font.render("MAC Address:", True, GREEN)
            self.screen.blit(label, (8, 40))
            hint2 = self.font.render("Format: AA:BB:CC:DD:EE:FF", True, DIM)
            self.screen.blit(hint2, (8, 55))
            inp = self.font.render(f"{self.mac_in}_", True, TEXT)
            self.screen.blit(inp, (8, 72))

        hint = self.font.render("ENTER=next  ESC=cancel", True, DIM)
        self.screen.blit(hint, (8, 228))
        pygame.display.flip()

    def draw(self):
        if self.mode == "list":
            self.draw_list()
        elif self.mode == "add":
            self.draw_add()

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if self.mode == "list":
                if event.key == pygame.K_DOWN:
                    self.selected = min(self.selected + 1, len(self.devices) - 1)
                elif event.key == pygame.K_UP:
                    self.selected = max(self.selected - 1, 0)
                elif event.key == pygame.K_RETURN:
                    if self.devices:
                        self.send_magic(self.devices[self.selected]["mac"])
                elif event.key == pygame.K_n:
                    self.mode    = "add"
                    self.stage   = "name"
                    self.name_in = ""
                    self.mac_in  = ""
                elif event.key == pygame.K_d:
                    if self.devices:
                        self.devices.pop(self.selected)
                        self.selected = max(0, self.selected - 1)
                        self.save()

            elif self.mode == "add":
                if self.stage == "name":
                    if event.key == pygame.K_RETURN and self.name_in:
                        self.stage = "mac"
                    elif event.key == pygame.K_BACKSPACE:
                        self.name_in = self.name_in[:-1]
                    elif event.key == pygame.K_ESCAPE:
                        self.mode = "list"
                    else:
                        self.name_in += event.unicode
                elif self.stage == "mac":
                    if event.key == pygame.K_RETURN and self.mac_in:
                        self.devices.append({
                            "name": self.name_in,
                            "mac" : self.mac_in
                        })
                        self.save()
                        self.mode   = "list"
                        self.status = f"Added {self.name_in}"
                    elif event.key == pygame.K_BACKSPACE:
                        self.mac_in = self.mac_in[:-1]
                    elif event.key == pygame.K_ESCAPE:
                        self.mode = "list"
                    else:
                        self.mac_in += event.unicode
