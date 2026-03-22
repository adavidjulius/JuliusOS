import pygame
import socket
import threading

BG     = (10, 10, 20)
TEXT   = (255, 255, 255)
ACCENT = (0, 200, 255)
GREEN  = (0, 255, 100)
DIM    = (80, 80, 80)

PORT = 9998

class Clipboard:
    def __init__(self, screen, font):
        self.screen  = screen
        self.font    = font
        self.content = ""
        self.log     = ["Julius Clipboard Sync"]
        self.my_ip   = self.get_ip()

    def get_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "0.0.0.0"

    def listen(self):
        def serve():
            srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            srv.bind(("0.0.0.0", PORT))
            srv.listen(1)
            self.log.append("Waiting for clipboard...")
            conn, addr = srv.accept()
            data = b""
            while True:
                chunk = conn.recv(4096)
                if not chunk:
                    break
                data += chunk
            self.content = data.decode()
            self.log.append(f"Received: {self.content[:30]}")
            conn.close()
            srv.close()
        t = threading.Thread(target=serve)
        t.daemon = True
        t.start()

    def push(self, ip, text):
        def send():
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((ip, PORT))
                s.sendall(text.encode())
                s.close()
                self.log.append(f"Pushed to {ip}")
            except Exception as e:
                self.log.append(f"Error: {e}")
        t = threading.Thread(target=send)
        t.daemon = True
        t.start()

    def draw(self):
        self.screen.fill(BG)
        title = self.font.render("Clipboard Sync", True, ACCENT)
        self.screen.blit(title, (8, 8))
        pygame.draw.line(self.screen, ACCENT, (0, 24), (240, 24), 1)

        ip_label = self.font.render(f"IP: {self.my_ip}", True, GREEN)
        self.screen.blit(ip_label, (8, 28))
        pygame.draw.line(self.screen, DIM, (0, 40), (240, 40), 1)

        y = 46
        for line in self.log[-8:]:
            surf = self.font.render(line[:30], True, TEXT)
            self.screen.blit(surf, (8, y))
            y += 17

        if self.content:
            preview = self.font.render(f"> {self.content[:28]}", True, GREEN)
            self.screen.blit(preview, (8, 190))

        hint = self.font.render("L=listen  P=push", True, DIM)
        self.screen.blit(hint, (8, 228))
        pygame.display.flip()

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_l:
                self.listen()
            elif event.key == pygame.K_p:
                self.push("192.168.1.100", self.content or "Hello from Julius OS")
