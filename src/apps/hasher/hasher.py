import pygame
import hashlib

BG     = (10, 10, 20)
TEXT   = (255, 255, 255)
ACCENT = (0, 200, 255)
GREEN  = (0, 255, 100)
DIM    = (80, 80,   80)
RED    = (255, 80,  80)

ALGOS = ["md5", "sha1", "sha256", "sha512"]

class Hasher:
    def __init__(self, screen, font):
        self.screen   = screen
        self.font     = font
        self.input    = ""
        self.results  = {}
        self.selected = 0
        self.mode     = "input"

    def compute(self):
        self.results = {}
        for algo in ALGOS:
            h = hashlib.new(algo)
            h.update(self.input.encode())
            self.results[algo] = h.hexdigest()
        self.mode = "result"

    def draw_input(self):
        self.screen.fill(BG)
        title = self.font.render("Hash Tool", True, ACCENT)
        self.screen.blit(title, (8, 8))
        pygame.draw.line(self.screen, ACCENT, (0, 24), (240, 24), 1)

        label = self.font.render("Enter text to hash:", True, GREEN)
        self.screen.blit(label, (8, 32))
        inp = self.font.render(f"{self.input[:26]}_", True, TEXT)
        self.screen.blit(inp, (8, 50))

        hint = self.font.render("ENTER=hash  ESC=clear", True, DIM)
        self.screen.blit(hint, (8, 228))
        pygame.display.flip()

    def draw_result(self):
        self.screen.fill(BG)
        title = self.font.render("Hash Results", True, ACCENT)
        self.screen.blit(title, (8, 8))
        pygame.draw.line(self.screen, ACCENT, (0, 24), (240, 24), 1)

        inp = self.font.render(f"Input: {self.input[:22]}", True, DIM)
        self.screen.blit(inp, (8, 28))
        pygame.draw.line(self.screen, DIM, (0, 40), (240, 40), 1)

        y = 46
        for i, (algo, digest) in enumerate(self.results.items()):
            color = ACCENT if i == self.selected else TEXT
            if i == self.selected:
                pygame.draw.rect(self.screen, (20, 40, 70), (4, y - 2, 232, 30), border_radius=4)
            al  = self.font.render(algo.upper(), True, color)
            dg1 = self.font.render(digest[:28],  True, GREEN)
            dg2 = self.font.render(digest[28:],  True, GREEN)
            self.screen.blit(al,  (8, y))
            self.screen.blit(dg1, (8, y + 10))
            if len(digest) > 28:
                self.screen.blit(dg2, (8, y + 20))
            y += 46

        hint = self.font.render("ESC=back  UP DOWN=select", True, DIM)
        self.screen.blit(hint, (8, 228))
        pygame.display.flip()

    def draw(self):
        if self.mode == "input":
            self.draw_input()
        elif self.mode == "result":
            self.draw_result()

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if self.mode == "input":
                if event.key == pygame.K_RETURN and self.input:
                    self.compute()
                elif event.key == pygame.K_BACKSPACE:
                    self.input = self.input[:-1]
                elif event.key == pygame.K_ESCAPE:
                    self.input = ""
                else:
                    self.input += event.unicode
            elif self.mode == "result":
                if event.key == pygame.K_ESCAPE:
                    self.mode  = "input"
                    self.input = ""
                elif event.key == pygame.K_DOWN:
                    self.selected = (self.selected + 1) % len(ALGOS)
                elif event.key == pygame.K_UP:
                    self.selected = (self.selected - 1) % len(ALGOS)
