import pygame
import socket
import subprocess
import threading

BG     = (10, 10, 20)
TEXT   = (255, 255, 255)
ACCENT = (0, 200, 255)
GREEN  = (0, 255, 100)
DIM    = (80, 80,   80)
RED    = (255, 80,  80)
YELLOW = (255, 200,  0)

class NetMapper:
    def __init__(self, screen, font):
        self.screen   = screen
        self.font     = font
        self.hosts    = []
        self.scanning = False
        self.status   = "Press S to scan network"
        self.selected = 0
        self.scroll   = 0
        self.progress = 0

    def get_local_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "192.168.1.1"

    def get_mac(self, ip):
        try:
            result = subprocess.check_output(
                ["arp", "-n", ip], stderr=subprocess.DEVNULL
            ).decode()
            for line in result.split("\n"):
                if ip in line:
                    parts = line.split()
                    for p in parts:
                        if ":" in p and len(p) == 17:
                            return p
        except:
            pass
        return "??:??:??:??:??:??"

    def get_hostname(self, ip):
        try:
            return socket.gethostbyaddr(ip)[0]
        except:
            return "Unknown"

    def scan(self):
        self.scanning = True
        self.hosts    = []
        self.progress = 0
        local_ip      = self.get_local_ip()
        base          = ".".join(local_ip.split(".")[:3])
        self.status   = f"Scanning {base}.0/24..."

        def run():
            for i in range(1, 255):
                ip     = f"{base}.{i}"
                result = subprocess.run(
                    ["ping", "-c", "1", "-W", "1", ip],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                self.progress = i
                if result.returncode == 0:
                    mac      = self.get_mac(ip)
                    hostname = self.get_hostname(ip)
                    self.hosts.append({
                        "ip"      : ip,
                        "mac"     : mac,
                        "hostname": hostname[:16]
                    })
            self.scanning = False
            self.status   = f"Found {len(self.hosts)} hosts"

        t = threading.Thread(target=run)
        t.daemon = True
        t.start()

    def draw(self):
        self.screen.fill(BG)
        title = self.font.render("Net Mapper", True, ACCENT)
        self.screen.blit(title, (8, 8))
        pygame.draw.line(self.screen, ACCENT, (0, 24), (240, 24), 1)

        color  = YELLOW if self.scanning else GREEN
        status = self.font.render(self.status, True, color)
        self.screen.blit(status, (8, 27))

        if self.scanning:
            bar_w = int(224 * self.progress / 254)
            pygame.draw.rect(self.screen, DIM,    (8, 38, 224, 6), border_radius=3)
            pygame.draw.rect(self.screen, ACCENT, (8, 38, bar_w, 6), border_radius=3)

        pygame.draw.line(self.screen, DIM, (0, 48), (240, 48), 1)

        header = self.font.render("IP              HOST", True, ACCENT)
        self.screen.blit(header, (8, 52))
        pygame.draw.line(self.screen, DIM, (0, 62), (240, 62), 1)

        y = 66
        for i, host in enumerate(self.hosts[self.scroll:self.scroll + 9]):
            idx   = i + self.scroll
            color = ACCENT if idx == self.selected else TEXT
            if idx == self.selected:
                pygame.draw.rect(self.screen, (20, 40, 70), (4, y - 1, 232, 26), border_radius=3)
            ip   = self.font.render(host["ip"],       True, color)
            hn   = self.font.render(host["hostname"], True, DIM)
            mac  = self.font.render(host["mac"],      True, GREEN)
            self.screen.blit(ip,  (8, y))
            self.screen.blit(hn,  (8, y + 13))
            y += 28

        hint = self.font.render("S=scan  UP DOWN=scroll", True, DIM)
        self.screen.blit(hint, (8, 228))
        pygame.display.flip()

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_s and not self.scanning:
                self.scan()
            elif event.key == pygame.K_DOWN:
                if self.selected < len(self.hosts) - 1:
                    self.selected += 1
                if self.selected >= self.scroll + 9:
                    self.scroll += 1
            elif event.key == pygame.K_UP:
                if self.selected > 0:
                    self.selected -= 1
                if self.selected < self.scroll:
                    self.scroll -= 1
