import pygame
import json
import os
import subprocess
import datetime

BG        = (18, 18, 22)
CARD      = (32, 32, 38)
WHITE     = (255, 255, 255)
DIM       = (120, 120, 130)
GREEN     = (48, 209, 88)
BLUE      = (10, 132, 255)
ORANGE    = (255, 159, 10)
PURPLE    = (191, 90, 242)
RED       = (255, 69, 58)
TEAL      = (90, 200, 250)

WIFI_STATE = "/var/run/julius_wifi.state"
BT_STATE   = "/var/run/julius_bt.state"

def read_state(path):
    state = {}
    if not os.path.exists(path):
        return state
    with open(path) as f:
        for line in f:
            line = line.strip()
            if "=" in line:
                k, v = line.split("=", 1)
                state[k.strip()] = v.strip()
    return state

class ControlCenter:
    def __init__(self, screen, font, font_small, cfg, save_cfg):
        self.screen    = screen
        self.font      = font
        self.font_small= font_small
        self.cfg       = cfg
        self.save_cfg  = save_cfg
        self.W         = screen.get_width()
        self.H         = screen.get_height()
        self.brightness= cfg.get("brightness", 80)
        self.volume    = cfg.get("volume", 70)
        self.visible   = False
        self.y_offset  = self.H
        self.anim_speed= 30

    def show(self):
        self.visible  = True
        self.y_offset = self.H

    def hide(self):
        self.visible  = False

    def toggle_wifi(self):
        self.cfg["wifi"] = not self.cfg.get("wifi", True)
        self.save_cfg(self.cfg)
        if self.cfg["wifi"]:
            subprocess.Popen(["julius_wifi_enable"])
        else:
            subprocess.Popen(["julius_wifi_disable"])

    def toggle_bt(self):
        self.cfg["bluetooth"] = not self.cfg.get("bluetooth", True)
        self.save_cfg(self.cfg)

    def toggle_airplane(self):
        self.cfg["airplane"] = not self.cfg.get("airplane", False)
        if self.cfg["airplane"]:
            self.cfg["wifi"]      = False
            self.cfg["bluetooth"] = False
        self.save_cfg(self.cfg)

    def toggle_hotspot(self):
        self.cfg["hotspot"] = not self.cfg.get("hotspot", False)
        self.save_cfg(self.cfg)

    def rr(self, color, rect, radius):
        x, y, w, h = rect
        r = min(radius, w//2, h//2)
        pygame.draw.rect(self.screen, color, (x+r, y, w-2*r, h))
        pygame.draw.rect(self.screen, color, (x, y+r, w, h-2*r))
        for cx, cy in [(x+r,y+r),(x+w-r,y+r),(x+r,y+h-r),(x+w-r,y+h-r)]:
            pygame.draw.circle(self.screen, color, (cx,cy), r)

    def draw_toggle(self, x, y, size, icon, label, active, color):
        bg = color if active else (50, 50, 58)
        self.rr(bg, (x, y, size, size), 16)
        ic = self.font_small.render(icon, True, WHITE)
        self.screen.blit(ic, (x+size//2-ic.get_width()//2,
                               y+size//2-ic.get_height()//2-4))
        lb = self.font_small.render(label, True, WHITE if active else DIM)
        self.screen.blit(lb, (x+size//2-lb.get_width()//2,
                               y+size-14))

    def draw_slider(self, x, y, w, h, val, color, label):
        self.rr(CARD, (x, y, w, h), h//2)
        fw = int((w-8) * val/100)
        self.rr(color, (x+4, y+4, fw, h-8), (h-8)//2)
        lb = self.font_small.render(label, True, WHITE)
        self.screen.blit(lb, (x, y-16))
        vl = self.font_small.render(f"{val}%", True, DIM)
        self.screen.blit(vl, (x+w-vl.get_width(), y-16))

    def draw(self):
        if not self.visible:
            return

        if self.y_offset > 0:
            self.y_offset = max(0, self.y_offset - self.anim_speed)

        panel_h = 320
        py      = self.H - panel_h + self.y_offset

        # Background blur simulation
        overlay = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        self.screen.blit(overlay, (0, 0))

        # Panel
        self.rr((22, 22, 28), (0, py, self.W, panel_h+10), 20)
        pygame.draw.line(self.screen, (50,50,60), (0,py), (self.W,py), 1)

        # Handle
        pygame.draw.rect(self.screen, (80,80,90),
            (self.W//2-25, py+8, 50, 4), border_radius=2)

        # Title
        now = datetime.datetime.now()
        tl  = self.font.render(now.strftime("%H:%M"), True, WHITE)
        self.screen.blit(tl, (self.W//2-tl.get_width()//2, py+20))

        # Connectivity toggles row 1
        tw   = self.W
        tsz  = 64
        tpad = (tw - tsz*4) // 5
        tx   = tpad
        ty   = py + 52

        wifi_state = read_state(WIFI_STATE)
        bt_state   = read_state(BT_STATE)

        wifi_on  = self.cfg.get("wifi",      True)
        bt_on    = self.cfg.get("bluetooth", True)
        air_on   = self.cfg.get("airplane",  False)
        hot_on   = self.cfg.get("hotspot",   False)

        toggles = [
            ("WiFi",  "W",  wifi_on,  BLUE,   self.toggle_wifi),
            ("BT",    "B",  bt_on,    BLUE,   self.toggle_bt),
            ("Air",   "✈",  air_on,   ORANGE, self.toggle_airplane),
            ("Spot",  "H",  hot_on,   GREEN,  self.toggle_hotspot),
        ]

        self.toggle_rects = []
        for i, (lbl, ic, active, col, _) in enumerate(toggles):
            rx = tpad + i*(tsz+tpad)
            self.draw_toggle(rx, ty, tsz, ic, lbl, active, col)
            self.toggle_rects.append((rx, ty, tsz, tsz, toggles[i][4]))

        # Row 2 toggles
        ty2  = ty + tsz + 10
        dark_on  = self.cfg.get("dark_mode",   True)
        notif_on = self.cfg.get("notifications",True)
        fp_on    = self.cfg.get("fingerprint",  True)
        ota_on   = self.cfg.get("ota_enabled",  True)

        toggles2 = [
            ("Dark",  "D", dark_on,  PURPLE, lambda: None),
            ("Notif", "N", notif_on, TEAL,   lambda: None),
            ("FP",    "F", fp_on,    GREEN,  lambda: None),
            ("OTA",   "O", ota_on,   ORANGE, lambda: None),
        ]
        for i, (lbl, ic, active, col, _) in enumerate(toggles2):
            rx = tpad + i*(tsz+tpad)
            self.draw_toggle(rx, ty2, tsz, ic, lbl, active, col)
            self.toggle_rects.append((rx, ty2, tsz, tsz, toggles2[i][4]))

        # Sliders
        sy1 = ty2 + tsz + 24
        self.draw_slider(16, sy1, self.W-32, 16,
            self.brightness, WHITE, "Brightness")
        self.draw_slider(16, sy1+44, self.W-32, 16,
            self.volume, TEAL, "Volume")

        # WiFi info
        if wifi_on and wifi_state.get("connected") == "1":
            ssid = wifi_state.get("ssid", "")
            ip   = wifi_state.get("ip",   "")
            info = self.font_small.render(
                f"WiFi: {ssid}  {ip}", True, (*GREEN, 200))
            self.screen.blit(info, (16, sy1+80))

    def handle_touch(self, pos):
        if not self.visible:
            return False
        panel_h = 320
        py      = self.H - panel_h

        if pos[1] < py:
            self.hide()
            return True

        for rx, ry, rw, rh, action in self.toggle_rects:
            if rx<=pos[0]<=rx+rw and ry<=pos[1]<=ry+rh:
                action()
                return True

        panel_bottom = self.H
        sy1 = py + 52 + 64*2 + 10*2 + 24
        # Brightness slider
        if 16<=pos[0]<=self.W-16 and sy1<=pos[1]<=sy1+16:
            val = int((pos[0]-16)/(self.W-32)*100)
            self.brightness     = max(0,min(100,val))
            self.cfg["brightness"] = self.brightness
            self.save_cfg(self.cfg)
            return True
        # Volume slider
        if 16<=pos[0]<=self.W-16 and sy1+44<=pos[1]<=sy1+60:
            val = int((pos[0]-16)/(self.W-32)*100)
            self.volume     = max(0,min(100,val))
            self.cfg["volume"] = self.volume
            self.save_cfg(self.cfg)
            return True

        return True
