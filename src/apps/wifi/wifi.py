import pygame
import subprocess

BG     = (10, 10, 20)
TEXT   = (255, 255, 255)
ACCENT = (0, 200, 255)

class WiFiScanner:
    def __init__(self, screen, font):
        self.screen   = screen
        self.font     = font
        self.networks = []

    def scan(self):
        try:
            result = subprocess.check_output(
                ["nmcli", "-t", "-f", "SSID,SIGNAL", "dev", "wifi"],
                stderr=subprocess.STDOUT
            ).decode()
            self.networks = []
            for line in result.strip().split("\n"):
                parts = line.split(":")
                if len(parts) >= 2:
                    self.networks.append({
                        "ssid"  : parts[0],
                        "signal": parts[1]
                    })
        except Exception as e:
            self.networks = [{"ssid": f"Error: {e}", "signal": ""}]

    def draw(self):
        self.screen.fill(BG)
        title = self.font.render("WiFi Scanner", True, ACCENT)
        self.screen.blit(title, (8, 8))
        pygame.draw.line(self.screen, ACCENT, (0, 24), (240, 24), 1)
        y = 32
        for net in self.networks[:12]:
            ssid   = self.font.render(net["ssid"][:22], True, TEXT)
            signal = self.font.render(net["signal"],    True, ACCENT)
            self.screen.blit(ssid,   (8,   y))
            self.screen.blit(signal, (200, y))
            y += 16
        if not self.networks:
            msg = self.font.render("Press S to scan", True, TEXT)
            self.screen.blit(msg, (50, 120))
        pygame.display.flip()

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_s:
                self.scan()
