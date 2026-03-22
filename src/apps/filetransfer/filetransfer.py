import pygame
import socket
import threading
import os

BG     = (10, 10, 20)
TEXT   = (255, 255, 255)
ACCENT = (0, 200, 255)
GREEN  = (0, 255, 100)
RED    = (255, 80, 80)
DIM    = (80, 80, 80)

PORT = 9999

class FileTransfer:
    def __init__(self, screen, font):
        self.screen   = screen
        self.font     = font
        self.log      = ["Julius File Transfer"]
        self.mode     = "menu"
        self.server   = None
        self.my_ip    = self.get_ip()

    def get_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "0.0.0.0"

    def start_server(self):
        def serve():
            self.log.append(f"Listening on {self.my_ip}:{PORT}")
            srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            srv.bind(("0.0.0.0", PORT))
            srv.listen(1)
            conn, addr = srv.accept()
            self.log.append(f"Connected: {addr[0]}")
            filename = conn.recv(1024).decode().strip()
            self.log.append(f"Receiving: {filename}")
            with open(f"/tmp/{filename}", "wb") as f:
                while True:
                    data = conn.recv(4096)
                    if not data:
                        break
                    f.write(data)
            self.log.append(f"Saved to /tmp/{filename}")
            conn.close()
            srv.close()
        t = threading.Thread(target=serve)
        t.daemon = True
        t.start()

    def send_file(self, ip, filepath):
        def send():
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((ip, PORT))
                filename = os.path.basename(filepath)
                s.send(filename.encode())
                with open(filepath, "rb") as f:
                    while True:
                        data = f.read(4096)
                        if not data:
                            break
                        s.send(data)
                s.close()
                self.log.append(f"Sent {filename} to {ip}")
            except Exception as e:
                self.log.append(f"Error: {e}")
        t = threading.Thread(target=send)
        t.daemon = True
        t.start()

    def draw(self):
        self.screen.fill(BG)
        title = self.font.render("File Transfer", True, ACCENT)
        self.screen.blit(title, (8, 8))
        pygame.draw.line(self.screen, ACCENT, (0, 24), (240, 24), 1)

        ip_label = self.font.render(f"My IP: {self.my_ip}", True, GREEN)
        self.screen.blit(ip_label, (8, 28))
        pygame.draw.line(self.screen, DIM, (0, 40), (240, 40), 1)

        y = 46
        for line in self.log[-10:]:
            surf = self.font.render(line[:30], True, TEXT)
            self.screen.blit(surf, (8, y))
            y += 17

        hint = self.font.render("R=receive  S=send", True, DIM)
        self.screen.blit(hint, (8, 228))
        pygame.display.flip()

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                self.start_server()
            elif event.key == pygame.K_s:
                self.send_file("192.168.1.100", "/tmp/test.txt")
