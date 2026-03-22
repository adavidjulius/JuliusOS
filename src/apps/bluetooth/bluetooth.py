import pygame
import subprocess

BG     = (10, 10, 20)
TEXT   = (255, 255, 255)
ACCENT = (80, 80, 255)

class BluetoothScanner:
    def __init__(self, screen, font):
        self.screen  = screen
        self.font    = font
        self.devices = []

    def scan(self):
        try:
            result = subprocess.check_output(
                ["hcitool", "scan"],
                stderr=subprocess.STDOUT
            ).decode()
            self.devices = []
            for line in result.strip().split("\n")[1:]:
                parts = line.strip().split("\t")
                if len(parts) >= 2:
                    self.devices.append({
                        "mac" : parts[0],
                        "name": parts[1]
                    })
        except Exception as e:
            self.devices = [{"mac": "Error", "name": str(e)}]

    def draw(self):
        self.screen.fill(BG)
        title = self.font.render("Bluetooth", True, ACCENT)
        self.screen.blit(title, (8, 8))
        pygame.draw.line(self.screen, ACCENT, (0, 24), (240, 24), 1)
        y = 32
        for dev in self.devices[:10]:
            name = self.font.render(dev["name"][:20], True, TEXT)
            mac  = self.font.render(dev["mac"],       True, ACCENT)
            self.screen.blit(name, (8, y))
            self.screen.blit(mac,  (8, y + 12))
            y += 30
        if not self.devices:
            msg = self.font.render("Press S to scan", True, TEXT)
            self.screen.blit(msg, (50, 120))
        pygame.display.flip()

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_s:
                self.scan()
