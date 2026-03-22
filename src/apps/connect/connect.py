import pygame
import socket
import subprocess
import json
import threading

BG     = (10, 10, 20)
TEXT   = (255, 255, 255)
ACCENT = (0, 200, 255)
GREEN  = (0, 255, 100)
DIM    = (80, 80, 80)

DEVICES = []

class DeviceConnect:
    def __init__(self, screen, font):
        self.screen  = screen
        self.font    = font
        self.devices = []
        self.selected = 0
        self.status  = "Press S to scan"
        self.scanning = False

    def scan_network(self):
        self.scanning = True
        self.status   = "Scanning..."
        self.devices  = []
        try:
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            base     = ".".join(local_ip.split(".")[:3])
            for i in range(1, 255):
                ip = f"{base}.{i}"
                result = subprocess.run(
                    ["ping", "-c", "1", "-W", "1", ip],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                if result.returncode == 0:
                    try:
                        name = socket.gethostbyaddr(ip)[0]
                    except:
                        name = "Unknown"
                    self.devices.append({"ip": ip, "name": name})
        except Exception as e:
            self.status = f"Error: {e}"
        self.scanning = False
        self.status   = f"Found {len(self.devices)} devices"

    def scan_thread(self):
        t = threading.Thread(target=self.scan_network)
        t.daemon = True
        t.start()

    def draw(self):
        self.screen.fill(BG)
        title = self.font.render("Device Connect", True, ACCENT)
        self.screen.blit(title, (8, 8))
        pygame.draw.line(self.screen, ACCENT, (0, 24), (240, 24), 1)

        status = self.font.render(self.status, True, GREEN)
        self.screen.blit(status, (8, 28))
        pygame.draw.line(self.screen, DIM, (0, 40), (240, 40), 1)

        y = 46
        for i, dev in enumerate(self.devices[:10]):
            color = ACCENT if i == self.selected else TEXT
            name  = self.font.render(dev["name"][:18], True, color)
            ip    = self.font.render(dev["ip"],        True, DIM)
            self.screen.blit(name, (8,   y))
            self.screen.blit(ip,   (140, y))
            y += 18

        self.screen.blit(hint, (8, 228))
        pygame.display.flip()

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_s:
                self.scan_thread()
            elif event.key == pygame.K_DOWN:
                self.selected = min(self.selected + 1, len(self.devices) - 1)
            elif event.key == pygame.K_UP:
                self.selected = max(self.selected - 1, 0)
            elif event.key == pygame.K_RETURN:
                if self.devices:
                    dev = self.devices[self.selected]
                    self.status = f"Connecting to {dev['ip']}..."
