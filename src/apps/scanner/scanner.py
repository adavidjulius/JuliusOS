import pygame
import socket
import threading
import subprocess

BG     = (10, 10, 20)
TEXT   = (255, 255, 255)
ACCENT = (0, 200, 255)
GREEN  = (0, 255, 100)
RED    = (255, 80,  80)
DIM    = (80, 80,   80)

class PortScanner:
    def __init__(self, screen, font):
        self.screen  = screen
        self.font    = font
        self.results = []
        self.status  = "Enter target IP"
        self.target  = ""
        self.typing  = True

    def scan(self, ip):
        self.status  = f"Scanning {ip}..."
        self.results = []
        COMMON_PORTS = [21,22,23,25,53,80,110,143,443,445,3306,3389,8080,8443]
        def run():
            for port in COMMON_PORTS:
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.settimeout(0.5)
                    result = s.connect_ex((ip, port))
                    if result == 0:
                        try:
                            service = socket.getservbyport(port)
                        except:
                            service = "unknown"
                        self.results.append({
                            "port"   : port,
                            "service": service,
                            "status" : "OPEN"
                        })
                    s.close()
                except:
                    pass
            self.status = f"Done — {len(self.results)} open ports"
        t = threading.Thread(target=run)
        t.daemon = True
        t.start()

    def draw(self):
        self.screen.fill(BG)
        title = self.font.render("Port Scanner", True, ACCENT)
        self.screen.blit(title, (8, 8))
        pygame.draw.line(self.screen, ACCENT, (0, 24), (240, 24), 1)

        status = self.font.render(self.status, True, GREEN)
        self.screen.blit(status, (8, 28))

        if self.typing:
            inp = self.font.render(f"IP: {self.target}_", True, TEXT)
            self.screen.blit(inp, (8, 44))
            hint = self.font.render("Type IP then ENTER to scan", True, DIM)
            self.screen.blit(hint, (8, 228))
        else:
            pygame.draw.line(self.screen, DIM, (0, 42), (240, 42), 1)
            y = 48
            for r in self.results[:9]:
                port    = self.font.render(str(r["port"]),    True, GREEN)
                service = self.font.render(r["service"][:12], True, TEXT)
                status  = self.font.render(r["status"],       True, GREEN)
                self.screen.blit(port,    (8,   y))
                self.screen.blit(service, (60,  y))
                self.screen.blit(status,  (185, y))
                y += 17
            hint = self.font.render("ESC=back  R=rescan", True, DIM)
            self.screen.blit(hint, (8, 228))

        pygame.display.flip()

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if self.typing:
                if event.key == pygame.K_RETURN and self.target:
                    self.typing = False
                    self.scan(self.target)
                elif event.key == pygame.K_BACKSPACE:
                    self.target = self.target[:-1]
                else:
                    if event.unicode in "0123456789.":
                        self.target += event.unicode
            else:
                if event.key == pygame.K_r:
                    self.scan(self.target)
                elif event.key == pygame.K_ESCAPE:
                    self.typing  = True
                    self.target  = ""
                    self.results = []
                    self.status  = "Enter target IP"
