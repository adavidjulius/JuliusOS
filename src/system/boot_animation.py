import pygame
import math
import time

WHITE  = (255, 255, 255)
BLACK  = (0,   0,   0)
BG     = (8,   8,  18)
ACCENT = (0,  200, 255)
PURPLE = (191,  90, 242)
GREEN  = (48,  209,  88)

class BootAnimation:
    def __init__(self, screen, W, H):
        self.screen = screen
        self.W      = W
        self.H      = H
        self.font_big   = pygame.font.SysFont("helvetica", 48, bold=True)
        self.font_med   = pygame.font.SysFont("helvetica", 18)
        self.font_small = pygame.font.SysFont("helvetica", 12)

    def rr(self, color, rect, radius):
        x, y, w, h = rect
        r = min(radius, w//2, h//2)
        pygame.draw.rect(self.screen, color, (x+r, y, w-2*r, h))
        pygame.draw.rect(self.screen, color, (x, y+r, w, h-2*r))
        for cx, cy in [(x+r,y+r),(x+w-r,y+r),(x+r,y+h-r),(x+w-r,y+h-r)]:
            pygame.draw.circle(self.screen, color, (cx,cy), r)

    def draw_julius_logo(self, cx, cy, size, alpha):
        s = pygame.Surface((size*3, size*3), pygame.SRCALPHA)
        sc = size*3//2

        # Outer ring
        pygame.draw.circle(s, (*ACCENT, alpha), (sc,sc), size, 3)

        # J letter
        font = pygame.font.SysFont("helvetica", size, bold=True)
        j    = font.render("J", True, (*WHITE, alpha))
        s.blit(j, (sc-j.get_width()//2, sc-j.get_height()//2))

        # Orbiting dots
        t = time.time()
        for i in range(3):
            ang = t*2 + i*(math.pi*2/3)
            dx  = int(math.cos(ang)*(size+8))
            dy  = int(math.sin(ang)*(size+8))
            col = [ACCENT, PURPLE, GREEN][i]
            pygame.draw.circle(s, (*col, alpha), (sc+dx, sc+dy), 4)

        self.screen.blit(s, (cx-size*3//2, cy-size*3//2))

    def play(self):
        W, H = self.W, self.H
        clock = pygame.time.Clock()

        # Phase 1 — black to logo fade in (1.5 sec)
        for frame in range(90):
            self.screen.fill(BG)
            alpha = min(255, int(frame * 3))
            t     = frame / 90.0

            # Pulse ring
            ring_size = int(20 + 15 * math.sin(t * math.pi * 2))
            self.draw_julius_logo(W//2, H//2 - 40, 36, alpha)

            # Julius OS text fade in
            if frame > 45:
                ta    = min(255, (frame-45)*6)
                title = self.font_big.render("Julius", True, (*WHITE, ta))
                os_t  = self.font_med.render("OS", True, (*ACCENT, ta))
                self.screen.blit(title,
                    (W//2 - title.get_width()//2, H//2 + 20))
                self.screen.blit(os_t,
                    (W//2 - os_t.get_width()//2, H//2 + 72))

            pygame.display.flip()
            clock.tick(60)

            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    return

        # Phase 2 — loading bar (1 sec)
        messages = [
            "Initializing kernel...",
            "Loading drivers...",
            "Starting services...",
            "Mounting filesystem...",
            "Starting Julius OS...",
        ]

        for i, msg in enumerate(messages):
            for frame in range(12):
                self.screen.fill(BG)
                self.draw_julius_logo(W//2, H//2 - 40, 36, 255)

                title = self.font_big.render("Julius", True, WHITE)
                os_t  = self.font_med.render("OS", True, ACCENT)
                self.screen.blit(title,
                    (W//2-title.get_width()//2, H//2+20))
                self.screen.blit(os_t,
                    (W//2-os_t.get_width()//2, H//2+72))

                # Messages
                for j, m in enumerate(messages[:i+1]):
                    col = WHITE if j == i else (60,60,70)
                    ms  = self.font_small.render(m, True, col)
                    self.screen.blit(ms,
                        (W//2-ms.get_width()//2, H//2+100+j*16))

                # Progress bar
                progress = (i * 12 + frame) / (len(messages) * 12)
                bar_w    = int((W-60) * progress)
                self.rr((40,40,50), (30, H-40, W-60, 6), 3)
                self.rr(ACCENT,     (30, H-40, bar_w, 6), 3)

                pygame.display.flip()
                clock.tick(60)

                for e in pygame.event.get():
                    if e.type == pygame.QUIT:
                        return

        # Phase 3 — flash to home
        for frame in range(20):
            alpha = int(frame * 12)
            overlay = pygame.Surface((W, H))
            overlay.fill(WHITE)
            overlay.set_alpha(min(255, alpha*3))
            self.screen.fill(BG)
            self.draw_julius_logo(W//2, H//2-40, 36, 255)
            title = self.font_big.render("Julius", True, WHITE)
            os_t  = self.font_med.render("OS", True, ACCENT)
            self.screen.blit(title,
                (W//2-title.get_width()//2, H//2+20))
            self.screen.blit(os_t,
                (W//2-os_t.get_width()//2, H//2+72))
            self.screen.blit(overlay, (0,0))
            pygame.display.flip()
            clock.tick(60)

            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    return
