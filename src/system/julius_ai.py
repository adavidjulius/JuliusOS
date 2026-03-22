import pygame
import threading
import json
import socket
import urllib.request
import urllib.parse
import os

BG     = (18, 18, 22)
CARD   = (28, 28, 34)
WHITE  = (255, 255, 255)
DIM    = (120, 120, 130)
BLUE   = (10, 132, 255)
GREEN  = (48, 209, 88)
PURPLE = (191, 90, 242)

class JuliusAI:
    def __init__(self, screen, font, font_small):
        self.screen     = screen
        self.font       = font
        self.font_small = font_small
        self.W          = screen.get_width()
        self.H          = screen.get_height()
        self.visible    = False
        self.messages   = []
        self.input      = ""
        self.thinking   = False
        self.scroll     = 0
        self.history    = [
            {"role":"system",
             "content":"You are Julius, an AI assistant built into "
                       "Julius OS — a custom mini handheld device. "
                       "Keep responses short and helpful. "
                       "You can help with device settings, "
                       "networking, security tools, and general questions."}
        ]

    def show(self):
        self.visible = True
        if not self.messages:
            self.messages.append({
                "role"   : "julius",
                "content": "Hi! I'm Julius, your AI assistant. How can I help?"
            })

    def hide(self):
        self.visible = False

    def ask(self, question):
        self.messages.append({"role":"user","content":question})
        self.thinking = True

        def run():
            try:
                self.history.append({"role":"user","content":question})
                payload = json.dumps({
                    "model"     : "claude-sonnet-4-20250514",
                    "max_tokens": 300,
                    "messages"  : self.history[-10:]
                }).encode()
                req = urllib.request.Request(
                    "https://api.anthropic.com/v1/messages",
                    data    = payload,
                    headers = {
                        "Content-Type"     : "application/json",
                        "anthropic-version": "2023-06-01",
                        "x-api-key"        : os.environ.get(
                            "JULIUS_AI_KEY","")
                    }
                )
                with urllib.request.urlopen(req, timeout=15) as resp:
                    data   = json.loads(resp.read())
                    answer = data["content"][0]["text"]
            except Exception as e:
                answer = f"Offline mode. ({str(e)[:40]})"

            self.history.append({"role":"assistant","content":answer})
            self.messages.append({"role":"julius","content":answer})
            self.thinking = False
            self.scroll   = max(0, len(self.messages)*60 - (self.H-200))

        threading.Thread(target=run, daemon=True).start()

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

        # Header
        pygame.draw.rect(self.screen,(22,22,28),(0,0,self.W,50))
        pygame.draw.line(self.screen,(50,50,60),(0,50),(self.W,50),1)

        j_ic = self.font.render("J", True, PURPLE)
        self.rr(PURPLE, (12,10,30,30), 8)
        j_ic2 = self.font.render("J", True, WHITE)
        self.screen.blit(j_ic2,(12+15-j_ic2.get_width()//2,
                                10+15-j_ic2.get_height()//2))
        title = self.font.render("Julius AI", True, WHITE)
        self.screen.blit(title,(50,15))

        if self.thinking:
            dots = "..." [:(int(pygame.time.get_ticks()/300)%4)]
            th   = self.font_small.render(f"Thinking{dots}", True, PURPLE)
            self.screen.blit(th,(self.W-th.get_width()-12,18))

        # Messages
        y = 60 - self.scroll
        for msg in self.messages:
            is_user = msg["role"] == "user"
            text    = msg["content"]
            lines   = []
            words   = text.split()
            line    = ""
            max_w   = 200
            for word in words:
                test = line + (" " if line else "") + word
                if self.font_small.size(test)[0] > max_w:
                    if line:
                        lines.append(line)
                    line = word
                else:
                    line = test
            if line:
                lines.append(line)

            bubble_h = len(lines)*16 + 16
            if y+bubble_h > 55 and y < self.H-60:
                if is_user:
                    bx = self.W - 220
                    self.rr(BLUE,(bx,y,210,bubble_h),12)
                    for j,ln in enumerate(lines):
                        ls = self.font_small.render(ln,True,WHITE)
                        self.screen.blit(ls,(bx+8,y+8+j*16))
                else:
                    self.rr(CARD,(10,y,210,bubble_h),12)
                    for j,ln in enumerate(lines):
                        ls = self.font_small.render(ln,True,WHITE)
                        self.screen.blit(ls,(18,y+8+j*16))
            y += bubble_h + 10

        # Input
        pygame.draw.rect(self.screen,(22,22,28),
            (0,self.H-52,self.W,52))
        pygame.draw.line(self.screen,(50,50,60),
            (0,self.H-52),(self.W,self.H-52),1)
        self.rr(CARD,(8,self.H-44,self.W-60,36),10)
        inp_text = self.input if self.input else "Ask Julius..."
        inp_col  = WHITE if self.input else (60,60,70)
        it = self.font_small.render(
            (self.input+"_")[:32] if self.input else inp_text,
            True, inp_col)
        self.screen.blit(it,(16,self.H-36))
        self.rr(BLUE,(self.W-52,self.H-46,44,38),10)
        send = self.font_small.render("Go",True,WHITE)
        self.screen.blit(send,
            (self.W-52+22-send.get_width()//2,
             self.H-46+19-send.get_height()//2))

    def handle_key(self, event):
        if not self.visible:
            return
        if event.key == pygame.K_RETURN and self.input.strip():
            self.ask(self.input.strip())
            self.input = ""
        elif event.key == pygame.K_BACKSPACE:
            self.input = self.input[:-1]
        elif event.key == pygame.K_ESCAPE:
            self.hide()
        elif event.unicode and event.unicode.isprintable():
            self.input += event.unicode

    def handle_touch(self, pos):
        if not self.visible:
            return
        W = self.W
        H = self.H
        if W-52<=pos[0]<=W-8 and H-46<=pos[1]<=H-8:
            if self.input.strip():
                self.ask(self.input.strip())
                self.input = ""
