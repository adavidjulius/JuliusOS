import pygame
import json
import os
import time
import threading

BG     = (18, 18, 22)
CARD   = (32, 32, 38)
WHITE  = (255, 255, 255)
DIM    = (120, 120, 130)
GREEN  = (48, 209, 88)
BLUE   = (10, 132, 255)
RED    = (255, 69, 58)
ORANGE = (255, 159, 10)

NOTIF_FILE = "/var/run/julius_notifications.json"

class NotificationCenter:
    def __init__(self, screen, font, font_small):
        self.screen     = screen
        self.font       = font
        self.font_small = font_small
        self.W          = screen.get_width()
        self.H          = screen.get_height()
        self.visible    = False
        self.y_offset   = -self.H
        self.notifs     = []
        self.scroll     = 0
        self.load()

    def load(self):
        if os.path.exists(NOTIF_FILE):
            with open(NOTIF_FILE) as f:
                try:
                    self.notifs = json.load(f)
                except:
                    self.notifs = []
        else:
            self.notifs = self.demo_notifs()

    def demo_notifs(self):
        now = time.strftime("%H:%M")
        return [
            {"app":"Julius OS", "title":"System Ready",
             "body":"All services running",
             "time":now,"color":[48,209,88],"read":False},
            {"app":"WiFi",  "title":"Connected",
             "body":"Connected to home network",
             "time":now,"color":[10,132,255],"read":False},
            {"app":"OTA",   "title":"Up to date",
             "body":"Julius OS v1.0 is current",
             "time":now,"color":[255,159,10],"read":True},
        ]

    def save(self):
        with open(NOTIF_FILE, "w") as f:
            json.dump(self.notifs, f)

    def add(self, app, title, body, color=None):
        self.notifs.insert(0, {
            "app"  : app,
            "title": title,
            "body" : body,
            "time" : time.strftime("%H:%M"),
            "color": color or [10,132,255],
            "read" : False,
        })
        if len(self.notifs) > 50:
            self.notifs = self.notifs[:50]
        self.save()

    def clear_all(self):
        self.notifs = []
        self.save()

    def mark_read(self, idx):
        if 0 <= idx < len(self.notifs):
            self.notifs[idx]["read"] = True
            self.save()

    def show(self):
        self.visible  = True
        self.y_offset = -300

    def hide(self):
        self.visible = False

    def unread_count(self):
        return sum(1 for n in self.notifs if not n["read"])

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

        if self.y_offset < 0:
            self.y_offset = min(0, self.y_offset + 25)

        panel_h = min(360, 80 + len(self.notifs)*72)
        py      = self.y_offset + 36

        overlay = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        self.screen.blit(overlay, (0, 0))

        self.rr((22, 22, 28), (0, py, self.W, panel_h), 20)
        pygame.draw.line(self.screen,(50,50,60),(0,py+panel_h),(self.W,py+panel_h),1)

        # Header
        hd = self.font.render("Notifications", True, WHITE)
        self.screen.blit(hd, (16, py+12))

        unread = self.unread_count()
        if unread > 0:
            badge = self.font_small.render(str(unread), True, WHITE)
            bx    = 16 + hd.get_width() + 8
            self.rr(RED, (bx-4, py+14, badge.get_width()+8, 18), 9)
            self.screen.blit(badge, (bx, py+16))

        cl = self.font_small.render("Clear", True, BLUE)
        self.screen.blit(cl, (self.W-cl.get_width()-16, py+16))
        self.clear_rect = (self.W-cl.get_width()-20, py+12,
                           cl.get_width()+8, 24)

        pygame.draw.line(self.screen,(50,50,60),(0,py+40),(self.W,py+40),1)

        if not self.notifs:
            empty = self.font_small.render("No notifications", True, DIM)
            self.screen.blit(empty,
                (self.W//2-empty.get_width()//2, py+60))
            return

        y   = py + 44 - self.scroll
        self.notif_rects = []
        for i, notif in enumerate(self.notifs):
            if y + 66 < py+40 or y > py+panel_h:
                y += 72
                self.notif_rects.append(None)
                continue
            col   = tuple(notif.get("color",[10,132,255]))
            alpha = 255 if not notif["read"] else 140
            bg    = (38,38,46) if not notif["read"] else (28,28,34)
            self.rr(bg, (8, y, self.W-16, 66), 12)
            pygame.draw.rect(self.screen, col, (8,y,3,66), border_radius=3)

            app_label = self.font_small.render(
                notif["app"], True, (*col, alpha))
            t_label   = self.font_small.render(
                notif["time"], True, (*DIM, alpha))
            ti_label  = self.font.render(
                notif["title"][:28], True, (*WHITE, alpha))
            bo_label  = self.font_small.render(
                notif["body"][:34], True, (*DIM, alpha))

            self.screen.blit(app_label, (18, y+6))
            self.screen.blit(t_label,
                (self.W-t_label.get_width()-16, y+6))
            self.screen.blit(ti_label, (18, y+22))
            self.screen.blit(bo_label, (18, y+42))
            self.notif_rects.append((8,y,self.W-16,66))
            y += 72

        # Scroll indicator
        if len(self.notifs) > 4:
            sb_h  = int(panel_h * panel_h / (len(self.notifs)*72))
            sb_y  = py+40 + int(self.scroll/(len(self.notifs)*72-panel_h)
                               *(panel_h-sb_h))
            pygame.draw.rect(self.screen,(80,80,90),
                (self.W-4,sb_y,3,sb_h),border_radius=2)

    def handle_touch(self, pos):
        if not self.visible:
            return False
        panel_h = min(360, 80+len(self.notifs)*72)
        py      = self.y_offset + 36

        if pos[1] > py+panel_h:
            self.hide()
            return True

        if hasattr(self,'clear_rect'):
            cr = self.clear_rect
            if cr[0]<=pos[0]<=cr[0]+cr[2] and cr[1]<=pos[1]<=cr[1]+cr[3]:
                self.clear_all()
                return True

        if hasattr(self,'notif_rects'):
            for i,rect in enumerate(self.notif_rects):
                if rect and rect[0]<=pos[0]<=rect[0]+rect[2] and \
                   rect[1]<=pos[1]<=rect[1]+rect[3]:
                    self.mark_read(i)
                    return True
        return True
