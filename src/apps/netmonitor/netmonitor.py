import pygame
import socket
import threading
import time
import subprocess

BG     = (10, 10, 20)
TEXT   = (255, 255, 255)
ACCENT = (0, 200, 255)
GREEN  = (0, 255, 100)
DIM    = (80, 80,   80)
RED    = (255, 80,  80)
YELLOW = (255, 200,  0)

class NetMonitor:
    def __init__(self, screen, font):
        self.screen   = screen
        self.font     = font
        self.stats    = []
        self.running  = False
        self.status   = "Press S to start"
        self.rx_old   = 0
        self.tx_old   = 0
        self.rx_speed = 0
        self.tx_speed = 0
        self.history  = []

    def get_bytes(self):
        try:
            with open("/proc/net/dev") as f:
                lines = f.readlines()
            rx = tx = 0
            for line in lines[2:]:
                parts = line.split()
                if len(parts) > 9:
                    rx += int(parts[1])
                    tx += int(parts[9])
            return rx, tx
        except:
            return 0, 0

    def get_connections(self):
        try:
            result = subprocess.check_output(
                ["ss", "-tuln"], stderr=subprocess.DEVNULL
            ).decode()
            conns = []
            for line in result.strip().split("\n")[1:6]:
                parts = line.split()
                if len(parts) >= 5:
                    conns.append({
                        "proto": parts[0],
                        "local": parts[4][-20:]
                    })
            return conns
        except:
            return []

    def monitor(self):
        self.running = True
        self.status  = "Monitoring..."
        while self.running:
            rx, tx         = self.get_bytes()
            self.rx_speed  = max(0, rx - self.rx_old)
            self.tx_speed  = max(0, tx - self.tx_old)
            self.rx_old    = rx
            self.tx_old    = tx
            self.history.append({
                "rx": self.rx_speed,
                "tx": self.tx_speed,
                "t" : time.strftime("%H:%M:%S")
            })
            if len(self.history) > 20:
                self.history.pop(0)
            self.stats = self.get_connections()
            time.sleep(1)

    def start(self):
        if not self.running:
            t = threading.Thread(target=self.monitor)
            t.daemon = True
            t.start()

    def stop(self):
        self.running = False
        self.status  = "Stopped"

    def fmt_bytes(self, b):
        if b > 1024 * 1024:
            return f"{b/1024/1024:.1f}MB/s"
        elif b > 1024:
            return f"{b/1024:.1f}KB/s"
        return f"{b}B/s"

    def draw(self):
        self.screen.fill(BG)
        title = self.font.render("Net Monitor", True, ACCENT)
        self.screen.blit(title, (8, 8))
        pygame.draw.line(self.screen, ACCENT, (0, 24), (240, 24), 1)

        color  = GREEN if self.running else RED
        status = self.font.render(self.status, True, color)
        self.screen.blit(status, (8, 27))
        pygame.draw.line(self.screen, DIM, (0, 38), (240, 38), 1)

        rx = self.font.render(f"RX: {self.fmt_bytes(self.rx_speed)}", True, GREEN)
        tx = self.font.render(f"TX: {self.fmt_bytes(self.tx_speed)}", True, YELLOW)
        self.screen.blit(rx, (8,   44))
        self.screen.blit(tx, (130, 44))
        pygame.draw.line(self.screen, DIM, (0, 58), (240, 58), 1)

        # Graph
        if self.history:
            max_val = max(max(h["rx"], h["tx"]) for h in self.history) or 1
            gx      = 8
            for i, h in enumerate(self.history[-20:]):
                rx_h = int(h["rx"] / max_val * 30)
                tx_h = int(h["tx"] / max_val * 30)
                pygame.draw.rect(screen, GREEN,  (gx, 92 - rx_h, 5, rx_h))
                pygame.draw.rect(screen, YELLOW, (gx, 92 - tx_h, 3, tx_h))
                gx += 11

        pygame.draw.line(self.screen, DIM, (0, 96), (240, 96), 1)

        conn_title = self.font.render("Connections:", True, ACCENT)
        self.screen.blit(conn_title, (8, 100))

        y = 114
        for conn in self.stats[:5]:
            proto = self.font.render(conn["proto"][:4], True, ACCENT)
            local = self.font.render(conn["local"],     True, TEXT)
            self.screen.blit(proto, (8,  y))
            self.screen.blit(local, (40, y))
            y += 16

        hint = self.font.render("S=start  X=stop", True, DIM)
        self.screen.blit(hint, (8, 228))
        pygame.display.flip()

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_s:
                self.start()
            elif event.key == pygame.K_x:
                self.stop()
