import pygame
import os
import subprocess

BG     = (18, 18, 22)
CARD   = (32, 32, 38)
WHITE  = (255, 255, 255)
DIM    = (100, 100, 110)
BLUE   = (10, 132, 255)
GREEN  = (48, 209, 88)

class Spotlight:
    def __init__(self, screen, font, font_small, apps):
        self.screen     = screen
        self.font       = font
        self.font_small = font_small
        self.apps       = apps
        self.W          = screen.get_width()
        self.H          = screen.get_height()
        self.visible    = False
        self.query      = ""
        self.results    = []
        self.selected   = 0

    def show(self):
        self.visible = True
        self.query   = ""
        self.results = []

    def hide(self):
        self.visible = False
        self.query   = ""

    def search(self, q):
        self.query   = q
        self.results = []
        if not q:
            return
        q_lower = q.lower()
        for app in self.apps:
            if q_lower in app["name"].lower():
                self.results.append({
                    "type" : "app",
                    "name" : app["name"],
                    "app"  : app,
                    "desc" : "Julius OS App",
                })
        cmds = ["nmap","ping","curl","python3","ls","cat","ps","df"]
        for cmd in cmds:
            if q_lower in cmd:
                self.results.append({
                    "type" : "command",
                    "name" : cmd,
                    "desc" : "Terminal Command",
                })
        if q_lower in ["wifi","network","ip"]:
            self.results.append({
                "type":"setting","name":"WiFi Settings",
                "desc":"Network Configuration"})
        if q_lower in ["bt","bluetooth"]:
            self.results.append({
                "type":"setting","name":"Bluetooth",
                "desc":"Bluetooth Settings"})

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

        overlay = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        # Search box
        self.rr((32,32,40), (12, 50, self.W-24, 44), 12)
        pygame.draw.rect(self.screen, BLUE,
            (12,50,self.W-24,44), 1, border_radius=12)

        ic = self.font_small.render("Search", True, DIM)
        self.screen.blit(ic, (24, 64))

        if self.query:
            qt = self.font.render(self.query+"_", True, WHITE)
        else:
            qt = self.font.render("Search apps, commands...", True,
                (60,60,70))
        self.screen.blit(qt, (80, 60))

        # Results
        if not self.results:
            if self.query:
                nm = self.font_small.render("No results", True, DIM)
                self.screen.blit(nm,
                    (self.W//2-nm.get_width()//2, 120))
            return

        self.result_rects = []
        y = 106
        for i, res in enumerate(self.results[:8]):
            bg = (42,42,52) if i==self.selected else (28,28,36)
            self.rr(bg, (12,y,self.W-24,46), 10)

            type_colors = {
                "app":"command","setting":"app","command":"setting"}
            tc = {"app":BLUE,"command":GREEN,"setting":(255,159,10)}
            col = tc.get(res["type"], BLUE)

            pygame.draw.rect(self.screen, col, (12,y,3,46), border_radius=2)
            nm = self.font.render(res["name"][:24], True, WHITE)
            ds = self.font_small.render(res["desc"],True, DIM)
            tp = self.font_small.render(res["type"].upper(),True,col)
            self.screen.blit(nm, (24, y+6))
            self.screen.blit(ds, (24, y+28))
            self.screen.blit(tp, (self.W-tp.get_width()-20, y+16))
            self.result_rects.append((12,y,self.W-24,46,res))
            y += 52

    def handle_key(self, event):
        if not self.visible:
            return None
        if event.key == pygame.K_ESCAPE:
            self.hide()
            return "hide"
        elif event.key == pygame.K_BACKSPACE:
            self.query = self.query[:-1]
            self.search(self.query)
        elif event.key == pygame.K_RETURN:
            if self.results and self.selected < len(self.results):
                return self.results[self.selected]
        elif event.key == pygame.K_DOWN:
            self.selected = min(self.selected+1, len(self.results)-1)
        elif event.key == pygame.K_UP:
            self.selected = max(self.selected-1, 0)
        else:
            if event.unicode and event.unicode.isprintable():
                self.query += event.unicode
                self.search(self.query)
                self.selected = 0
        return None

    def handle_touch(self, pos):
        if not self.visible:
            return None
        if hasattr(self, "result_rects"):
            for rx,ry,rw,rh,res in self.result_rects:
                if rx<=pos[0]<=rx+rw and ry<=pos[1]<=ry+rh:
                    return res
        if pos[1] < 50 or pos[1] > 106 + len(self.results)*52:
            self.hide()
        return None
