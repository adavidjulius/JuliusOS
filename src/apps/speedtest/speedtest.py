import pygame
import socket
import threading
import time
import urllib.request

BG     = (10, 10, 20)
TEXT   = (255, 255, 255)
ACCENT = (0, 200, 255)
GREEN  = (0, 255, 100)
DIM    = (80, 80,   80)
RED    = (255, 80,  80)
YELLOW = (255, 200,  0)

class SpeedTest:
    def __init__(self, screen, font):
        self.screen    = screen
        self.font      = font
        self.status    = "Press S to start test"
        self.download  = 0.0
        self.ping      = 0
        self.running   = False
        self.log       = ["Julius Speed Test v0.4"]

    def measure_ping(self, host="8.8.8.8"):
        try:
            start = time.time()
            s     = socket.create_connection((host, 53), timeout=2)
            s.close()
            return round((time.time() - start) * 1000, 1)
        except:
            return -1

    def measure_download(self):
        try:
            url   = "http://speedtest.tele2.net/1MB.zip"
            start = time.time()
            urllib.request.urlretrieve(url, "/tmp/julius_speedtest.bin")
            elapsed = time.time() - start
            mbps    = round((1 * 8) / elapsed, 2)
            return mbps
        except Exception as e:
            self.log.append(f"DL Error: {e}")
            return 0.0

    def run(self):
        self.running  = True
        self.status   = "Testing ping..."
        self.log.append("Starting test...")

        self.ping     = self.measure_ping()
        self.log.append(f"Ping: {self.ping}ms")
        self.status   = "Testing download..."

        self.download = self.measure_download()
        self.log.append(f"Download: {self.download} Mbps")

        self.status  = "Test complete"
        self.running = False

    def start(self):
        if not self.running:
            t = threading.Thread(target=self.run)
            t.daemon = True
            t.start()

    def draw(self):
        self.screen.fill(BG)
        title = self.font.render("Speed Test", True, ACCENT)
        self.screen.blit(title, (8, 8))
        pygame.draw.line(self.screen, ACCENT, (0, 24), (240, 24), 1)

        color  = YELLOW if self.running else GREEN
        status = self.font.render(self.status, True, color)
        self.screen.blit(status, (8, 28))
        pygame.draw.line(self.screen, DIM, (0, 40), (240, 40), 1)

        ping_label = self.font.render(f"Ping     : {self.ping} ms",       True, TEXT)
        dl_label   = self.font.render(f"Download : {self.download} Mbps", True, TEXT)
        self.screen.blit(ping_label, (8, 50))
        self.screen.blit(dl_label,   (8, 68))
        pygame.draw.line(self.screen, DIM, (0, 84), (240, 84), 1)

        y = 90
        for line in self.log[-8:]:
            surf = self.font.render(line[:30], True, DIM)
            self.screen.blit(surf, (8, y))
            y += 17

        hint = self.font.render("S=start test", True, DIM)
        self.screen.blit(hint, (8, 228))
        pygame.display.flip()

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_s:
                self.start()
