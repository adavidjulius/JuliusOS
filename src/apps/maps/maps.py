import pygame
import socket
import subprocess
import threading
import math
import json
import os

BG     = (8,   8,  18)
CARD   = (22,  22,  28)
WHITE  = (255, 255, 255)
DIM    = (100, 100, 110)
ACCENT = (0,  200, 255)
GREEN  = (48,  209,  88)
RED    = (255,  69,  58)
YELLOW = (255, 200,  10)
ORANGE = (255, 159,  10)

class NetworkMap:
    def __init__(self, screen, font):
        self.screen     = screen
        self.font       = font
        self.font_med   = pygame.font.SysFont("helvetica", 13)
        self.font_small = pygame.font.SysFont("helvetica", 10)
        self.W          = screen.get_width()
        self.H          = screen.get_height()
        self.hosts      = []
        self.scanning   = False
        self.status     = "Press S to scan network"
        self.selected   = None
        self.mode       = "map"
        self.progress   = 0
        self.my_ip      = self.get_ip()
        self.scroll_y   = 0
        self.zoom       = 1.0
        self.pan_x      = 0
        self.pan_y      = 0
        self.host_detail= None

    def get_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8",80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "0.0.0.0"

    def get_mac(self, ip):
        try:
            result = subprocess.check_output(
                ["arp","-n",ip],
                stderr=subprocess.DEVNULL
            ).decode()
            for line in result.split("\n"):
                if ip in line:
                    parts = line.split()
                    for p in parts:
                        if ":" in p and len(p)==17:
                            return p
        except:
            pass
        return "??:??:??:??:??:??"

    def get_hostname(self, ip):
        try:
            return socket.gethostbyaddr(ip)[0]
        except:
            return "Unknown"

    def detect_type(self, ip, hostname):
        hn = hostname.lower()
        if "router" in hn or "gateway" in hn:
            return "router", RED
        elif "phone" in hn or "android" in hn or "iphone" in hn:
            return "phone", GREEN
        elif "laptop" in hn or "mac" in hn or "pc" in hn:
            return "computer", ACCENT
        elif "tv" in hn or "smart" in hn:
            return "tv", ORANGE
        elif "printer" in hn:
            return "printer", YELLOW
        else:
            return "device", DIM

    def scan(self):
        self.scanning = True
        self.hosts    = []
        self.progress = 0
        base          = ".".join(self.my_ip.split(".")[:3])
        self.status   = f"Scanning {base}.0/24..."

        def run():
            threads = []
            lock    = threading.Lock()

            def ping(i):
                ip  = f"{base}.{i}"
                res = subprocess.run(
                    ["ping","-c","1","-W","1",ip],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                with lock:
                    self.progress = i
                if res.returncode == 0:
                    mac      = self.get_mac(ip)
                    hostname = self.get_hostname(ip)
                    dtype, color = self.detect_type(ip, hostname)
                    angle    = len(self.hosts) * (2*math.pi/8)
                    radius   = 80 if dtype != "router" else 0
                    with lock:
                        self.hosts.append({
                            "ip"      : ip,
                            "mac"     : mac,
                            "hostname": hostname[:16],
                            "type"    : dtype,
                            "color"   : color,
                            "angle"   : angle,
                            "radius"  : radius,
                            "open_ports": [],
                        })

            for i in range(1,255):
                t = threading.Thread(target=ping,args=(i,))
                t.daemon = True
                threads.append(t)
                t.start()
                if len(threads) >= 20:
                    for th in threads:
                        th.join()
                    threads = []

            for th in threads:
                th.join()

            self.scanning = False
            self.status   = f"Found {len(self.hosts)} hosts"

            # Redistribute angles
            for i,h in enumerate(self.hosts):
                h["angle"]  = i*(2*math.pi/max(1,len(self.hosts)))
                h["radius"] = 0 if h["type"]=="router" else 80+i%3*20

        threading.Thread(target=run, daemon=True).start()

    def scan_ports(self, host):
        def run():
            ports = [21,22,23,25,53,80,443,445,3306,8080]
            open_ports = []
            for p in ports:
                try:
                    s = socket.socket(
                        socket.AF_INET,socket.SOCK_STREAM)
                    s.settimeout(0.3)
                    if s.connect_ex((host["ip"],p)) == 0:
                        open_ports.append(p)
                    s.close()
                except:
                    pass
            host["open_ports"] = open_ports
        threading.Thread(target=run,daemon=True).start()

    def rr(self, color, rect, radius):
        x, y, w, h = rect
        r = min(radius, w//2, h//2)
        pygame.draw.rect(self.screen, color, (x+r, y, w-2*r, h))
        pygame.draw.rect(self.screen, color, (x, y+r, w, h-2*r))
        for cx, cy in [(x+r,y+r),(x+w-r,y+r),(x+r,y+h-r),(x+w-r,y+h-r)]:
            pygame.draw.circle(self.screen, color, (cx,cy), r)

    def draw_map_view(self):
        W, H = self.W, self.H
        self.screen.fill(BG)

        # Grid background
        for gx in range(0, W, 20):
            pygame.draw.line(self.screen,(18,18,26),
                (gx,40),(gx,H-60),1)
        for gy in range(40, H-60, 20):
            pygame.draw.line(self.screen,(18,18,26),
                (0,gy),(W,gy),1)

        # Status bar area
        pygame.draw.rect(self.screen,(14,14,22),(0,0,W,40))
        pygame.draw.line(self.screen,(40,40,50),
            (0,40),(W,40),1)

        title = self.font_med.render("Network Map",True,WHITE)
        self.screen.blit(title,(12,12))

        col2 = YELLOW if self.scanning else GREEN
        st   = self.font.render(self.status,True,col2)
        self.screen.blit(st,(12,28))

        if self.scanning:
            bar_w = int((W-24)*self.progress/254)
            self.rr((40,40,50),(12,34,W-24,4),2)
            self.rr(ACCENT,(12,34,bar_w,4),2)

        # Center point (this device)
        cx2 = W//2 + self.pan_x
        cy2 = H//2 + self.pan_y - 10

        # Range rings
        for ring in [60,100,140]:
            pygame.draw.circle(self.screen,
                (25,25,35),(cx2,cy2),
                int(ring*self.zoom),1)

        # Connection lines to hosts
        self.host_rects = []
        for host in self.hosts:
            hx = cx2 + int(math.cos(host["angle"]) *
                           host["radius"] * self.zoom)
            hy = cy2 + int(math.sin(host["angle"]) *
                           host["radius"] * self.zoom)
            pygame.draw.line(self.screen,
                (*host["color"],60),(cx2,cy2),(hx,hy),1)
            is_sel = self.selected == host["ip"]
            radius = 12 if is_sel else 8
            pygame.draw.circle(self.screen,
                host["color"],(hx,hy),radius)
            if is_sel:
                pygame.draw.circle(self.screen,
                    WHITE,(hx,hy),radius+3,2)

            ip_label = self.font.render(
                host["ip"].split(".")[-1],True,WHITE)
            self.screen.blit(ip_label,
                (hx-ip_label.get_width()//2,hy-6))
            self.host_rects.append((hx-12,hy-12,24,24,host))

        # This device
        pygame.draw.circle(self.screen,ACCENT,(cx2,cy2),14)
        me = self.font.render("ME",True,WHITE)
        self.screen.blit(me,
            (cx2-me.get_width()//2,cy2-me.get_height()//2))
        ip_me = self.font.render(self.my_ip,True,(*ACCENT,180))
        self.screen.blit(ip_me,
            (cx2-ip_me.get_width()//2,cy2+18))

        # Bottom toolbar
        pygame.draw.rect(self.screen,(14,14,22),
            (0,H-52,W,52))
        pygame.draw.line(self.screen,(40,40,50),
            (0,H-52),(W,H-52),1)

        btns = [
            ("Scan", W//5,   H-30),
            ("List", W*2//5, H-30),
            ("Zoom+",W*3//5, H-30),
            ("Zoom-",W*4//5, H-30),
        ]
        self.btn_rects = []
        for lbl,bx,by in btns:
            bw = 52
            bh = 26
            self.rr(CARD,(bx-bw//2,by-bh//2,bw,bh),8)
            lt = self.font.render(lbl,True,WHITE)
            self.screen.blit(lt,
                (bx-lt.get_width()//2,
                 by-lt.get_height()//2))
            self.btn_rects.append(
                (bx-bw//2,by-bh//2,bw,bh,lbl))

        # Selected host detail panel
        if self.selected:
            host = next(
                (h for h in self.hosts
                 if h["ip"]==self.selected),None)
            if host:
                self.rr((22,28,36),
                    (8,H-130,W-16,72),10)
                pygame.draw.rect(self.screen,
                    host["color"],(8,H-130,3,72),
                    border_radius=3)
                hn = self.font_med.render(
                    host["hostname"],True,WHITE)
                ip2 = self.font.render(
                    host["ip"],True,host["color"])
                mc  = self.font.render(
                    host["mac"],True,DIM)
                tp  = self.font.render(
                    host["type"].upper(),True,host["color"])
                self.screen.blit(hn,(16,H-126))
                self.screen.blit(ip2,(16,H-110))
                self.screen.blit(mc,(16,H-96))
                self.screen.blit(tp,(W-tp.get_width()-16,H-126))
                if host["open_ports"]:
                    pts = self.font.render(
                        "Ports: "+
                        ",".join(map(str,host["open_ports"][:5])),
                        True,YELLOW)
                    self.screen.blit(pts,(16,H-82))
                else:
                    scan_h = self.font.render(
                        "Tap to scan ports",True,DIM)
                    self.screen.blit(scan_h,(16,H-82))

    def draw_list_view(self):
        W, H = self.W, self.H
        self.screen.fill(BG)
        pygame.draw.rect(self.screen,(14,14,22),(0,0,W,40))
        pygame.draw.line(self.screen,(40,40,50),(0,40),(W,40),1)

        title = self.font_med.render("Host List",True,WHITE)
        self.screen.blit(title,(12,12))
        count = self.font.render(
            f"{len(self.hosts)} hosts",True,DIM)
        self.screen.blit(count,(W-count.get_width()-12,14))

        self.list_rects = []
        y = 44 - self.scroll_y
        for host in self.hosts:
            if y+46 < 40 or y > H-52:
                y += 50
                self.list_rects.append(None)
                continue
            is_sel = self.selected == host["ip"]
            bg     = (30,38,52) if is_sel else CARD
            self.rr(bg,(8,y,W-16,44),8)
            pygame.draw.rect(self.screen,host["color"],
                (8,y,3,44),border_radius=3)

            hn  = self.font_med.render(
                host["hostname"][:18],True,WHITE)
            ip3 = self.font.render(host["ip"],True,DIM)
            tp2 = self.font.render(
                host["type"].upper(),True,host["color"])
            self.screen.blit(hn,(16,y+6))
            self.screen.blit(ip3,(16,y+26))
            self.screen.blit(tp2,(W-tp2.get_width()-16,y+16))
            self.list_rects.append((8,y,W-16,44,host))
            y += 50

        pygame.draw.rect(self.screen,(14,14,22),(0,H-52,W,52))
        pygame.draw.line(self.screen,(40,40,50),
            (0,H-52),(W,H-52),1)
        back = self.font_med.render("Map View",True,ACCENT)
        self.screen.blit(back,(W//2-back.get_width()//2,H-34))

    def draw(self):
        if self.mode == "map":
            self.draw_map_view()
        else:
            self.draw_list_view()
        pygame.display.flip()

    def handle_input(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = event.pos
            if self.mode == "map":
                if hasattr(self,"btn_rects"):
                    for bx,by,bw,bh,lbl in self.btn_rects:
                        if (bx<=pos[0]<=bx+bw and
                                by<=pos[1]<=by+bh):
                            if lbl == "Scan":
                                self.scan()
                            elif lbl == "List":
                                self.mode = "list"
                            elif lbl == "Zoom+":
                                self.zoom = min(2.0,self.zoom+0.2)
                            elif lbl == "Zoom-":
                                self.zoom = max(0.5,self.zoom-0.2)
                            return

                if hasattr(self,"host_rects"):
                    for hx,hy,hw,hh,host in self.host_rects:
                        if (hx<=pos[0]<=hx+hw and
                                hy<=pos[1]<=hy+hh):
                            if self.selected == host["ip"]:
                                self.scan_ports(host)
                            else:
                                self.selected = host["ip"]
                            return

            else:
                if hasattr(self,"list_rects"):
                    for item in self.list_rects:
                        if item is None:
                            continue
                        rx,ry,rw,rh,host = item
                        if (rx<=pos[0]<=rx+rw and
                                ry<=pos[1]<=ry+rh):
                            self.selected = host["ip"]
                            self.mode     = "map"
                            return
                if pos[1] > self.H-52:
                    self.mode = "map"

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_s:
                self.scan()
            elif event.key == pygame.K_l:
                self.mode = "list" if self.mode=="map" else "map"
