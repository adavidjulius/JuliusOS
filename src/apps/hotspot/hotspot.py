import pygame
import subprocess

BG     = (10, 10, 20)
TEXT   = (255, 255, 255)
ACCENT = (0, 200, 255)
GREEN  = (0, 255, 100)
RED    = (255, 80, 80)
DIM    = (80, 80, 80)

class Hotspot:
    def __init__(self, screen, font):
        self.screen = screen
        self.font   = font
        self.active = False
        self.log    = ["Julius Hotspot"]
        self.ssid   = "JuliusOS"
        self.passwd = "julius123"

    def start(self):
        try:
            subprocess.run([
                "nmcli", "dev", "wifi", "hotspot",
                "ifname", "wlan0",
                "ssid",   self.ssid,
                "password", self.passwd
            ])
            self.active = True
            self.log.append(f"Hotspot ON: {self.ssid}")
            self.log.append(f"Pass: {self.passwd}")
        except Exception as e:
            self.log.append(f"Error: {e}")

    def stop(self):
        try:
            subprocess.run(["nmcli", "con", "down", self.ssid])
            self.active = False
            self.log.append("Hotspot OFF")
        except Exception as e:
            self.log.append(f"Error: {e}")

    def draw(self):
        self.screen.fill(BG)
        title = self.font.render("Hotspot", True, ACCENT)
        self.screen.blit(title, (8, 8))
        pygame.draw.line(self.screen, ACCENT, (0, 24), (240, 24), 1)

        color  = GREEN if self.active else RED
        status = self.font.render(
            f"Status: {'ACTIVE' if self.active else 'OFF'}", True, color
        )
        self.screen.blit(status, (8, 30))

        ssid_l = self.font.render(f"SSID: {self.ssid}",     True, TEXT)
        pass_l = self.font.render(f"Pass: {self.passwd}",   True, TEXT)
        self.screen.blit(ssid_l, (8, 50))
        self.screen.blit(pass_l, (8, 68))
        pygame.draw.line(self.screen, DIM, (0, 84), (240, 84), 1)

        y = 90
        for line in self.log[-8:]:
            surf = self.font.render(line[:30], True, DIM)
            self.screen.blit(surf, (8, y))
            y += 17

        hint = self.font.render("S=start  X=stop", True, DIM)
        self.screen.blit(hint, (8, 228))
        pygame.display.flip()

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_s:
                self.start()
            elif event.key == pygame.K_x:
                self.stop()
