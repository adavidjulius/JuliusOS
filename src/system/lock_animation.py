import pygame
import math
import time

WHITE  = (255, 255, 255)
GREEN  = (48,  209,  88)
BLUE   = (10,  132, 255)
RED    = (255,  69,  58)
PURPLE = (191,  90, 242)
DIM    = (120, 120, 130)
BG     = (8,    8,  18)

class LockAnimation:
    def __init__(self, screen, W, H):
        self.screen   = screen
        self.W        = W
        self.H        = H
        self.state    = "idle"
        self.progress = 0.0
        self.start_t  = 0
        self.result   = None
        self.particles= []

    def start_scan(self):
        self.state    = "scanning"
        self.progress = 0.0
        self.start_t  = time.time()
        self.result   = None

    def set_result(self, success):
        self.state  = "result"
        self.result = success
        self.start_t= time.time()
        if success:
            self.spawn_particles()

    def spawn_particles(self):
        import random
        cx = self.W//2
        cy = self.H//2
        for _ in range(24):
            angle = random.uniform(0, math.pi*2)
            speed = random.uniform(2, 8)
            self.particles.append({
                "x"    : cx,
                "y"    : cy,
                "vx"   : math.cos(angle)*speed,
                "vy"   : math.sin(angle)*speed,
                "life" : 1.0,
                "color": random.choice([GREEN,BLUE,WHITE,PURPLE])
            })

    def update(self):
        elapsed = time.time() - self.start_t
        if self.state == "scanning":
            self.progress = min(1.0, elapsed/2.0)
            if self.progress >= 1.0:
                self.state = "waiting"
        elif self.state == "result":
            for p in self.particles:
                p["x"]    += p["vx"]
                p["y"]    += p["vy"]
                p["vy"]   += 0.3
                p["life"] -= 0.03
            self.particles = [p for p in self.particles if p["life"]>0]
            if elapsed > 1.5 and not self.particles:
                self.state = "done"

    def draw(self):
        self.update()
        cx = self.W//2
        cy = self.H//2

        if self.state == "idle":
            # Fingerprint icon
            t = time.time()
            pulse = 0.7 + 0.3*math.sin(t*2)
            col   = tuple(int(c*pulse) for c in DIM)
            self.draw_fingerprint(cx, cy, 40, col)
            hint = pygame.font.SysFont("helvetica",12).render(
                "Touch to unlock", True, DIM)
            self.screen.blit(hint,
                (cx-hint.get_width()//2, cy+55))

        elif self.state in ["scanning","waiting"]:
            # Scanning animation
            t   = time.time()
            col = BLUE
            self.draw_fingerprint(cx, cy, 40, col)

            # Scan line
            scan_y = cy-40 + int(80*self.progress)
            pygame.draw.line(self.screen, (*BLUE,180),
                (cx-35,scan_y),(cx+35,scan_y),2)

            # Progress ring
            angle = self.progress * math.pi * 2
            for i in range(int(angle/(math.pi*2)*60)):
                a  = i/60*math.pi*2 - math.pi/2
                px = cx + int(math.cos(a)*48)
                py = cy + int(math.sin(a)*48)
                pygame.draw.circle(self.screen, BLUE, (px,py), 2)

            wait = pygame.font.SysFont("helvetica",12).render(
                "Scanning...", True, BLUE)
            self.screen.blit(wait,(cx-wait.get_width()//2,cy+58))

        elif self.state == "result":
            if self.result:
                self.draw_fingerprint(cx, cy, 40, GREEN)
                ok = pygame.font.SysFont("helvetica",14,bold=True).render(
                    "Unlocked", True, GREEN)
                self.screen.blit(ok,(cx-ok.get_width()//2,cy+58))
            else:
                self.draw_fingerprint(cx, cy, 40, RED)
                fail = pygame.font.SysFont("helvetica",14,bold=True).render(
                    "Not recognized", True, RED)
                self.screen.blit(fail,
                    (cx-fail.get_width()//2,cy+58))

            for p in self.particles:
                alpha = int(p["life"]*255)
                col   = (*p["color"][:3],)
                pygame.draw.circle(self.screen, col,
                    (int(p["x"]),int(p["y"])), 3)

    def draw_fingerprint(self, cx, cy, size, color):
        # Draw fingerprint lines
        lines = [
            [(0,-size),(0,size)],
            [(-size*0.5,-size*0.8),(size*0.5,-size*0.8)],
            [(-size*0.8,-size*0.4),(size*0.8,-size*0.4)],
            [(-size,-0),(size,0)],
            [(-size*0.8,size*0.4),(size*0.8,size*0.4)],
            [(-size*0.5,size*0.8),(size*0.5,size*0.8)],
        ]
        for i,(s,e) in enumerate(lines):
            opacity  = 200 - i*20
            sx, sy   = cx+int(s[0]*0.6), cy+int(s[1]*0.6)
            ex, ey   = cx+int(e[0]*0.6), cy+int(e[1]*0.6)
            pygame.draw.line(self.screen,color,(sx,sy),(ex,ey),2)

        # Outer ring
        pygame.draw.circle(self.screen,color,(cx,cy),size,2)
        pygame.draw.circle(self.screen,color,(cx,cy),size-8,1)
        pygame.draw.circle(self.screen,color,(cx,cy),size-18,1)

    def is_done(self):
        return self.state == "done"
