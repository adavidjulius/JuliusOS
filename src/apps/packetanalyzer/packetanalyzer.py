import pygame
import socket
import threading

BG     = (10, 10, 20)
TEXT   = (255, 255, 255)
ACCENT = (0, 200, 255)
GREEN  = (0, 255, 100)
DIM    = (80, 80,   80)
RED    = (255, 80,  80)
YELLOW = (255, 200,  0)

class PacketAnalyzer:
    def __init__(self, screen, font):
        self.screen   = screen
        self.font     = font
        self.packets  = []
        self.running  = False
        self.status   = "Press S to start"

    def start(self):
        self.running = True
        self.status  = "Capturing on your network..."
        def capture():
            try:
                s = socket.socket(
                    socket.AF_INET,
                    socket.SOCK_RAW,
                    socket.IPPROTO_IP
                )
                s.bind((self.get_ip(), 0))
                s.settimeout(1)
                while self.running:
                    try:
                        data, addr = s.recvfrom(1024)
                        src  = addr[0]
                        size = len(data)
                        proto = data[9] if len(data) > 9 else 0
                        name  = {6: "TCP", 17: "UDP", 1: "ICMP"}.get(proto, f"#{proto}")
                        self.packets.append({
                            "src"  : src,
                            "size" : size,
                            "proto": name
                        })
                        if len(self.packets) > 50:
                            self.packets.pop(0)
                    except socket.timeout:
                        continue
            except Exception as e:
                self.status  = f"Error: {e}"
                self.running = False
        t = threading.Thread(target=capture)
        t.daemon = True
        t.start()

    def stop(self):
        self.running = False
        self.status  = "Stopped"

    def get_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "0.0.0.0"

    def draw(self):
        self.screen.fill(BG)
        title = self.font.render("Packet Analyzer", True, ACCENT)
        self.screen.blit(title, (8, 8))
        pygame.draw.line(self.screen, ACCENT, (0, 24), (240, 24), 1)

        color  = GREEN if self.running else RED
        status = self.font.render(self.status, True, color)
        self.screen.blit(status, (8, 28))
        pygame.draw.line(self.screen, DIM, (0, 40), (240, 40), 1)

        header = self.font.render("SRC            PROTO  SIZE", True, ACCENT)
        self.screen.blit(header, (8, 43))
        pygame.draw.line(self.screen, DIM, (0, 54), (240, 54), 1)

        y = 57
        for pkt in self.packets[-10:]:
            src   = self.font.render(pkt["src"][:15],  True, TEXT)
            proto = self.font.render(pkt["proto"][:5], True, YELLOW)
            size  = self.font.render(str(pkt["size"]), True, GREEN)
            self.screen.blit(src,   (8,   y))
            self.screen.blit(proto, (130, y))
            self.screen.blit(size,  (190, y))
            y += 16

        count = self.font.render(f"Total: {len(self.packets)} packets", True, DIM)
        self.screen.blit(count, (8, 210))

        hint = self.font.render("S=start  X=stop  C=clear", True, DIM)
        self.screen.blit(hint, (8, 228))
        pygame.display.flip()

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_s:
                self.start()
            elif event.key == pygame.K_x:
                self.stop()
            elif event.key == pygame.K_c:
                self.packets = []
