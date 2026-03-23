import pygame
import time
import math

BG     = (8,   8,  18)
CARD   = (22,  22,  28)
WHITE  = (255, 255, 255)
DIM    = (100, 100, 110)
ACCENT = (0,  200, 255)
RED    = (255,  69,  58)

class AppSwitcher:
    def __init__(self, screen, W, H, app_instances, APPS):
        self.screen       = screen
        self.W            = W
        self.H            = H
        self.app_instances= app_instances
        self.APPS         = APPS
        self.visible      = False
        self.recent       = []
        self.selected     = 0
        self.font         = pygame.font.SysFont("helvetica", 12)
        self.font_small   = pygame.font.SysFont("helvetica", 10)
        self.scroll_x     = 0
        self.target_x     = 0
        self.snapshots    = {}

    def add_recent(self, app_name):
        if app_name in self.recent:
            self.recent.remove(app_name)
        self.recent.insert(0, app_name)
        if len(self.recent) > 8:
            self.recent = self.recent[:8]

    def take_snapshot(self, app_name):
        snap = pygame.Surface((self.W, self.H))
        snap.blit(self.screen, (0,0))
        self.snapshots[app_name] = snap

    def show(self):
        self.visible  = True
        self.scroll_x = 0
        self.target_x = 0
        self.selected = 0

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

        # Smooth scroll
        self.scroll_x += (self.target_x - self.scroll_x) * 0.2

        # Dark overlay
        overlay = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0,0))

        # Title
        title = self.font.render("App Switcher", True, WHITE)
        self.screen.blit(title,
            (self.W//2-title.get_width()//2, 20))

        if not self.recent:
            empty = self.font.render("No recent apps", True, DIM)
            self.screen.blit(empty,
                (self.W//2-empty.get_width()//2, self.H//2))
            hint = self.font_small.render(
                "Swipe up and hold to open", True, DIM)
            self.screen.blit(hint,
                (self.W//2-hint.get_width()//2, self.H-30))
            return

        card_w = 160
        card_h = 260
        gap    = 20
        total  = len(self.recent)
        start_x= self.W//2 - card_w//2 - int(self.scroll_x)

        self.card_rects = []

        for i, app_name in enumerate(self.recent):
            x = start_x + i*(card_w+gap) - (total//2)*(card_w+gap)
            y = self.H//2 - card_h//2 + 20

            is_selected = (i == self.selected)
            scale       = 1.05 if is_selected else 1.0
            sw          = int(card_w*scale)
            sh          = int(card_h*scale)
            sx          = x - (sw-card_w)//2
            sy          = y - (sh-card_h)//2

            if sx > self.W+100 or sx+sw < -100:
                self.card_rects.append(None)
                continue

            # Card background
            self.rr(CARD, (sx, sy, sw, sh), 16)

            if is_selected:
                pygame.draw.rect(self.screen, ACCENT,
                    (sx, sy, sw, sh), 2, border_radius=16)

            # App snapshot or colored preview
            app = next((a for a in self.APPS if a["name"]==app_name), None)
            if app_name in self.snapshots:
                snap = pygame.transform.scale(
                    self.snapshots[app_name], (sw-8, sh-40))
                self.screen.blit(snap, (sx+4, sy+4))
            elif app:
                preview = pygame.Surface((sw-8, sh-40))
                preview.fill(app["bg"])
                ac = app["ac"]
                pygame.draw.circle(preview, ac,
                    ((sw-8)//2, (sh-40)//2), 30, 3)
                self.screen.blit(preview, (sx+4, sy+4))

            # App name
            lbl = self.font.render(app_name, True, WHITE)
            self.screen.blit(lbl,
                (sx+sw//2-lbl.get_width()//2, sy+sh-26))

            # Close button
            close_x = sx+sw-18
            close_y = sy+6
            pygame.draw.circle(self.screen, RED,
                (close_x, close_y), 10)
            cl = self.font_small.render("x", True, WHITE)
            self.screen.blit(cl,
                (close_x-cl.get_width()//2,
                 close_y-cl.get_height()//2))

            self.card_rects.append({
                "rect"  : (sx, sy, sw, sh),
                "close" : (close_x-10, close_y-10, 20, 20),
                "name"  : app_name,
                "index" : i
            })

        # Bottom hint
        hint = self.font_small.render(
            "Swipe left/right  |  Tap to open  |  X to close",
            True, DIM)
        self.screen.blit(hint,
            (self.W//2-hint.get_width()//2, self.H-24))

    def handle_touch(self, pos, is_swipe_left=False,
                     is_swipe_right=False):
        if not self.visible:
            return None

        if is_swipe_left:
            self.selected = min(self.selected+1, len(self.recent)-1)
            self.target_x += 180
            return None

        if is_swipe_right:
            self.selected = max(self.selected-1, 0)
            self.target_x -= 180
            return None

        if not hasattr(self, "card_rects"):
            return None

        for card in self.card_rects:
            if card is None:
                continue
            cr = card["close"]
            if (cr[0]<=pos[0]<=cr[0]+cr[2] and
                    cr[1]<=pos[1]<=cr[1]+cr[3]):
                name = card["name"]
                self.recent.remove(name)
                if name in self.snapshots:
                    del self.snapshots[name]
                return "closed"

            r = card["rect"]
            if (r[0]<=pos[0]<=r[0]+r[2] and
                    r[1]<=pos[1]<=r[1]+r[3]):
                self.hide()
                return card["name"]

        return None
