import pygame
import subprocess
import threading
import math
import time

BG     = (8,   8,  18)
CARD   = (22,  22,  28)
WHITE  = (255, 255, 255)
DIM    = (100, 100, 110)
ACCENT = (0,  200, 255)
GREEN  = (48,  209,  88)
RED    = (255,  69,  58)
ORANGE = (255, 159,  10)

PRESETS = [
    {"name": "Radio Mirchi",  "freq": 98.3,  "city": "Chennai"},
    {"name": "Sun FM",        "freq": 93.5,  "city": "Chennai"},
    {"name": "Big FM",        "freq": 92.7,  "city": "Chennai"},
    {"name": "Radio City",    "freq": 91.1,  "city": "Chennai"},
    {"name": "AIR FM",        "freq": 100.1, "city": "Chennai"},
    {"name": "Red FM",        "freq": 93.5,  "city": "Chennai"},
    {"name": "Rainbow FM",    "freq": 101.9, "city": "Chennai"},
    {"name": "Hello FM",      "freq": 106.4, "city": "Chennai"},
]

class Radio:
    def __init__(self, screen, font):
        self.screen   = screen
        self.font     = font
        self.font_big = pygame.font.SysFont("helvetica", 32, bold=True)
        self.font_med = pygame.font.SysFont("helvetica", 16)
        self.W        = screen.get_width()
        self.H        = screen.get_height()
        self.freq     = 98.3
        self.playing  = False
        self.selected = 0
        self.mode     = "presets"
        self.signal   = 0
        self.process  = None
        self.status   = "Ready"
        self.scan_results = []
        self.volume   = 80
        self.visualizer = [0]*20
        self.t        = 0

    def play(self, freq):
        self.stop()
        self.freq    = freq
        self.playing = True
        self.status  = f"Playing {freq} MHz"
        def run():
            try:
                self.process = subprocess.Popen(
                    ["rtl_fm", "-f", f"{freq}M",
                     "-M", "fm", "-s", "200000",
                     "-r", "44100", "-",
                     "|", "aplay", "-r", "44100",
                     "-f", "S16_LE"],
                    shell=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                self.process.wait()
            except Exception as e:
                self.status  = f"Error: {str(e)[:20]}"
                self.playing = False
        threading.Thread(target=run, daemon=True).start()

    def stop(self):
        if self.process:
            try:
                self.process.terminate()
            except:
                pass
        self.playing = False
        self.status  = "Stopped"

    def scan(self):
        self.status = "Scanning..."
        self.scan_results = []
        def run():
            for f in range(880, 1080):
                freq = f / 10.0
                self.scan_results.append(freq)
                time.sleep(0.05)
            self.status = f"Found {len(self.scan_results)} stations"
        threading.Thread(target=run, daemon=True).start()

    def update_visualizer(self):
        self.t += 0.1
        if self.playing:
            for i in range(len(self.visualizer)):
                base = math.sin(self.t + i*0.5) * 0.5 + 0.5
                self.visualizer[i] = base * 40 + 5
        else:
            for i in range(len(self.visualizer)):
                self.visualizer[i] = max(2, self.visualizer[i]-2)

    def rr(self, color, rect, radius):
        x, y, w, h = rect
        r = min(radius, w//2, h//2)
        pygame.draw.rect(self.screen, color, (x+r, y, w-2*r, h))
        pygame.draw.rect(self.screen, color, (x, y+r, w, h-2*r))
        for cx, cy in [(x+r,y+r),(x+w-r,y+r),(x+r,y+h-r),(x+w-r,y+h-r)]:
            pygame.draw.circle(self.screen, color, (cx,cy), r)

    def draw_player(self):
        W, H = self.W, self.H
        self.update_visualizer()

        self.screen.fill(BG)
        pygame.draw.rect(self.screen,(14,14,22),(0,0,W,180))

        # Frequency display
        freq_str = f"{self.freq:.1f}"
        mhz_str  = "MHz"
        ft  = self.font_big.render(freq_str, True, WHITE)
        mt  = self.font_med.render(mhz_str, True, ACCENT)
        self.screen.blit(ft, (W//2-ft.get_width()//2-20, 46))
        self.screen.blit(mt, (W//2+ft.get_width()//2-16, 68))

        # Station name
        preset = next(
            (p for p in PRESETS if abs(p["freq"]-self.freq)<0.1),
            None)
        if preset:
            sn = self.font_med.render(preset["name"], True, ACCENT)
            self.screen.blit(sn, (W//2-sn.get_width()//2, 90))

        # Status
        st = self.font.render(self.status, True,
            GREEN if self.playing else DIM)
        self.screen.blit(st, (W//2-st.get_width()//2, 112))

        # Visualizer bars
        bar_w   = (W-40)//len(self.visualizer) - 2
        bar_y   = 160
        for i, h2 in enumerate(self.visualizer):
            bx  = 20 + i*(bar_w+2)
            col = ACCENT if self.playing else (40,40,50)
            pygame.draw.rect(self.screen, col,
                (bx, bar_y-int(h2), bar_w, int(h2)),
                border_radius=2)

        pygame.draw.line(self.screen,(40,40,50),
            (0,168),(W,168),1)

        # Controls
        cy2 = 196
        btn_data = [
            ("-0.1", W//2-120, cy2),
            ("PREV", W//2-64,  cy2),
            ("PLAY" if not self.playing else "STOP",
             W//2-20, cy2),
            ("NEXT", W//2+24,  cy2),
            ("+0.1", W//2+68,  cy2),
        ]
        self.control_rects = []
        for lbl,bx,by in btn_data:
            is_main = lbl in ["PLAY","STOP"]
            bw      = 48 if is_main else 40
            bh      = 36 if is_main else 30
            col     = ACCENT if is_main else CARD
            self.rr(col, (bx, by, bw, bh), 8)
            lt = self.font.render(lbl, True, WHITE)
            self.screen.blit(lt,
                (bx+bw//2-lt.get_width()//2,
                 by+bh//2-lt.get_height()//2))
            self.control_rects.append((bx,by,bw,bh,lbl))

        # Volume slider
        vol_y = 242
        vl    = self.font.render(f"Vol: {self.volume}%",True,DIM)
        self.screen.blit(vl,(20,vol_y-14))
        self.rr((40,40,50),(20,vol_y,W-40,8),4)
        fw = int((W-40)*self.volume/100)
        self.rr(ACCENT,(20,vol_y,fw,8),4)
        pygame.draw.circle(self.screen,WHITE,(20+fw,vol_y+4),6)
        self.vol_rect = (20,vol_y-6,W-40,20)

        # Presets header
        ph = self.font_med.render("Presets", True, WHITE)
        self.screen.blit(ph,(20,264))
        pygame.draw.line(self.screen,(40,40,50),
            (0,282),(W,282),1)

        # Preset list
        self.preset_rects = []
        y = 286
        for i,p in enumerate(PRESETS[:5]):
            is_sel = abs(p["freq"]-self.freq)<0.1
            bg     = (30,40,55) if is_sel else CARD
            self.rr(bg,(8,y,W-16,34),8)
            if is_sel:
                pygame.draw.rect(self.screen,ACCENT,
                    (8,y,W-16,34),1,border_radius=8)
            nm = self.font.render(p["name"],True,WHITE)
            fq = self.font.render(
                f"{p['freq']} MHz",True,
                ACCENT if is_sel else DIM)
            self.screen.blit(nm,(16,y+10))
            self.screen.blit(fq,(W-fq.get_width()-16,y+10))
            self.preset_rects.append(
                (8,y,W-16,34,p["freq"]))
            y += 40

        pygame.display.flip()

    def draw(self):
        self.draw_player()

    def handle_input(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = event.pos
            if hasattr(self,"control_rects"):
                for bx,by,bw,bh,lbl in self.control_rects:
                    if bx<=pos[0]<=bx+bw and by<=pos[1]<=by+bh:
                        if lbl == "PLAY":
                            self.play(self.freq)
                        elif lbl == "STOP":
                            self.stop()
                        elif lbl == "-0.1":
                            self.freq = round(
                                max(87.5,self.freq-0.1),1)
                        elif lbl == "+0.1":
                            self.freq = round(
                                min(108.0,self.freq+0.1),1)
                        elif lbl == "PREV":
                            self.selected = max(
                                0,self.selected-1)
                            self.freq = PRESETS[
                                self.selected]["freq"]
                        elif lbl == "NEXT":
                            self.selected = min(
                                len(PRESETS)-1,
                                self.selected+1)
                            self.freq = PRESETS[
                                self.selected]["freq"]

            if hasattr(self,"preset_rects"):
                for rx,ry,rw,rh,freq in self.preset_rects:
                    if rx<=pos[0]<=rx+rw and ry<=pos[1]<=ry+rh:
                        self.play(freq)

            if hasattr(self,"vol_rect"):
                vr = self.vol_rect
                if (vr[0]<=pos[0]<=vr[0]+vr[2] and
                        vr[1]<=pos[1]<=vr[1]+vr[3]):
                    self.volume = int(
                        (pos[0]-20)/(self.W-40)*100)
                    self.volume = max(0,min(100,self.volume))
