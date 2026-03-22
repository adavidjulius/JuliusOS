import pygame
import socket
import threading
import os
import json

BG     = (18, 18, 22)
CARD   = (28, 28, 34)
WHITE  = (255, 255, 255)
DIM    = (120, 120, 130)
BLUE   = (10, 132, 255)
GREEN  = (48, 209, 88)
TEAL   = (90, 200, 250)

DROP_PORT   = 9977
DROP_DIR    = "/var/julius/drops/"
BROADCAST   = "255.255.255.255"

class JuliusDrop:
    def __init__(self, screen, font, font_small):
        self.screen      = screen
        self.font        = font
        self.font_small  = font_small
        self.W           = screen.get_width()
        self.H           = screen.get_height()
        self.visible     = False
        self.nearby      = []
        self.transfers   = []
        self.status      = "Ready"
        self.mode        = "menu"
        self.my_name     = socket.gethostname()
        self.receiving   = False
        os.makedirs(DROP_DIR, exist_ok=True)
        self.start_receiver()
        self.start_beacon()

    def get_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "0.0.0.0"

    def start_beacon(self):
        def beacon():
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            while True:
                msg = json.dumps({
                    "name": self.my_name,
                    "ip"  : self.get_ip(),
                    "type": "julius_drop"
                }).encode()
                try:
                    s.sendto(msg, (BROADCAST, DROP_PORT-1))
                except:
                    pass
                threading.Event().wait(5)
        threading.Thread(target=beacon, daemon=True).start()

        def listen():
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind(("", DROP_PORT-1))
            except:
                return
            while True:
                try:
                    data, addr = s.recvfrom(1024)
                    info = json.loads(data.decode())
                    if info.get("type") == "julius_drop":
                        if info["ip"] != self.get_ip():
                            existing = [d["ip"] for d in self.nearby]
                            if info["ip"] not in existing:
                                self.nearby.append(info)
                except:
                    pass
        threading.Thread(target=listen, daemon=True).start()

    def start_receiver(self):
        def receive():
            srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                srv.bind(("", DROP_PORT))
                srv.listen(5)
            except:
                return
            while True:
                try:
                    conn, addr = srv.accept()
                    self.handle_receive(conn, addr)
                except:
                    pass
        threading.Thread(target=receive, daemon=True).start()

    def handle_receive(self, conn, addr):
        try:
            header = b""
            while b"\n" not in header:
                header += conn.recv(1)
            info     = json.loads(header.decode().strip())
            filename = info["name"]
            filesize = info["size"]
            filepath = os.path.join(DROP_DIR, filename)
            received = 0
            with open(filepath, "wb") as f:
                while received < filesize:
                    data = conn.recv(min(4096, filesize-received))
                    if not data:
                        break
                    f.write(data)
                    received += len(data)
            self.transfers.append({
                "name"     : filename,
                "from"     : addr[0],
                "size"     : filesize,
                "direction": "received",
                "status"   : "done"
            })
            self.status = f"Received {filename}"
        except Exception as e:
            self.status = f"Receive error: {e}"
        finally:
            conn.close()

    def send_file(self, ip, filepath):
        def send():
            try:
                filename = os.path.basename(filepath)
                filesize = os.path.getsize(filepath)
                s        = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((ip, DROP_PORT))
                header   = json.dumps({
                    "name": filename,
                    "size": filesize
                }) + "\n"
                s.sendall(header.encode())
                with open(filepath, "rb") as f:
                    while True:
                        chunk = f.read(4096)
                        if not chunk:
                            break
                        s.sendall(chunk)
                s.close()
                self.transfers.append({
                    "name"     : filename,
                    "to"       : ip,
                    "size"     : filesize,
                    "direction": "sent",
                    "status"   : "done"
                })
                self.status = f"Sent {filename}"
            except Exception as e:
                self.status = f"Send error: {e}"
        threading.Thread(target=send, daemon=True).start()

    def show(self):
        self.visible = True
        self.mode    = "menu"

    def hide(self):
        self.visible = False

    def rr(self, color, rect, radius):
        x, y, w, h = rect
        r = min(radius, w//2, h//2)
        pygame.draw.rect(self.screen, color, (x+r, y, w-2*r, h))
        pygame.draw.rect(self.screen, color, (x, y+r, w, h-2*r))
        for cx, cy in [(x+r,y+r),(x+w-r,y+r),(x+r,y+h-r),(x+w-r,y+h-r)]:
            pygame.draw.circle(self.screen, color, (cx,cy), r)

    def draw(self):
        if not self.visible:
            return
        self.screen.fill(BG)
        pygame.draw.rect(self.screen,(22,22,28),(0,0,self.W,50))
        pygame.draw.line(self.screen,(50,50,60),(0,50),(self.W,50),1)

        title = self.font.render("Julius Drop", True, WHITE)
        self.screen.blit(title,(self.W//2-title.get_width()//2,14))

        st = self.font_small.render(self.status, True, TEAL)
        self.screen.blit(st,(self.W//2-st.get_width()//2,36))

        # My device
        me_label = self.font_small.render(
            f"This device: {self.my_name}", True, DIM)
        self.screen.blit(me_label,(12,58))
        ip_label = self.font_small.render(
            f"IP: {self.get_ip()}", True, (*DIM,150))
        self.screen.blit(ip_label,(12,72))

        # Nearby devices
        nearby_title = self.font.render("Nearby Devices", True, WHITE)
        self.screen.blit(nearby_title,(12,94))
        pygame.draw.line(self.screen,(50,50,60),(0,112),(self.W,112),1)

        self.device_rects = []
        if not self.nearby:
            nm = self.font_small.render(
                "Scanning for Julius devices...", True, DIM)
            self.screen.blit(nm,(12,122))
        else:
            y = 116
            for dev in self.nearby[:4]:
                self.rr(CARD,(8,y,self.W-16,46),10)
                nm = self.font.render(dev["name"][:20],True,WHITE)
                ip = self.font_small.render(dev["ip"],True,DIM)
                self.screen.blit(nm,(18,y+6))
                self.screen.blit(ip,(18,y+28))
                send_btn = self.font_small.render("Send",True,WHITE)
                self.rr(BLUE,(self.W-60,y+10,52,28),8)
                self.screen.blit(send_btn,
                    (self.W-60+26-send_btn.get_width()//2,
                     y+10+14-send_btn.get_height()//2))
                self.device_rects.append(
                    (8,y,self.W-16,46,dev["ip"]))
                y += 52

        # Recent transfers
        if self.transfers:
            tl = self.font.render("Recent", True, WHITE)
            ty = 116 + max(len(self.nearby),1)*52 + 10
            self.screen.blit(tl,(12,ty))
            pygame.draw.line(self.screen,(50,50,60),
                (0,ty+18),(self.W,ty+18),1)
            for tr in self.transfers[-3:]:
                ty += 24
                arrow = "↓" if tr["direction"]=="received" else "↑"
                col   = GREEN if tr["direction"]=="received" else BLUE
                trt   = self.font_small.render(
                    f"{arrow} {tr['name'][:20]}", True, col)
                self.screen.blit(trt,(12,ty))

    def handle_touch(self, pos):
        if not self.visible:
            return
        if hasattr(self,"device_rects"):
            for rx,ry,rw,rh,ip in self.device_rects:
                if self.W-60<=pos[0]<=self.W-8 and ry+10<=pos[1]<=ry+38:
                    self.status = f"Select file to send to {ip}"
                    return
