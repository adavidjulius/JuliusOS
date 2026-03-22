import pygame
import base64
import urllib.parse

BG     = (10, 10, 20)
TEXT   = (255, 255, 255)
ACCENT = (0, 200, 255)
GREEN  = (0, 255, 100)
DIM    = (80, 80,   80)
RED    = (255, 80,  80)

MODES = ["Base64 Enc", "Base64 Dec", "URL Enc", "URL Dec", "Hex Enc", "Hex Dec"]

class Encoder:
    def __init__(self, screen, font):
        self.screen   = screen
        self.font     = font
        self.input    = ""
        self.output   = ""
        self.selected = 0
        self.mode     = "menu"
        self.status   = ""

    def process(self):
        try:
            mode = MODES[self.selected]
            if mode == "Base64 Enc":
                self.output = base64.b64encode(self.input.encode()).decode()
            elif mode == "Base64 Dec":
                self.output = base64.b64decode(self.input.encode()).decode()
            elif mode == "URL Enc":
                self.output = urllib.parse.quote(self.input)
            elif mode == "URL Dec":
                self.output = urllib.parse.unquote(self.input)
            elif mode == "Hex Enc":
                self.output = self.input.encode().hex()
            elif mode == "Hex Dec":
                self.output = bytes.fromhex(self.input).decode()
            self.status = "Done"
        except Exception as e:
            self.output = f"Error: {e}"
            self.status = "Error"

    def draw_menu(self):
        self.screen.fill(BG)
        title = self.font.render("Encoder", True, ACCENT)
        self.screen.blit(title, (8, 8))
        pygame.draw.line(self.screen, ACCENT, (0, 24), (240, 24), 1)

        y = 32
        for i, mode in enumerate(MODES):
            color = ACCENT if i == self.selected else TEXT
            if i == self.selected:
                pygame.draw.rect(self.screen, (20, 40, 70), (4, y - 1, 232, 15), border_radius=4)
            label = self.font.render(mode, True, color)
            self.screen.blit(label, (8, y))
            y += 22

        hint = self.font.render("UP DOWN=select  ENTER=use", True, DIM)
        self.screen.blit(hint, (8, 228))
        pygame.display.flip()

    def draw_input(self):
        self.screen.fill(BG)
        mode  = MODES[self.selected]
        title = self.font.render(mode, True, ACCENT)
        self.screen.blit(title, (8, 8))
        pygame.draw.line(self.screen, ACCENT, (0, 24), (240, 24), 1)

        in_l  = self.font.render("Input:", True, GREEN)
        self.screen.blit(in_l, (8, 30))
        inp   = self.font.render(f"{self.input[:26]}_", True, TEXT)
        self.screen.blit(inp, (8, 44))
        pygame.draw.line(self.screen, DIM, (0, 62), (240, 62), 1)

        out_l = self.font.render("Output:", True, GREEN)
        self.screen.blit(out_l, (8, 68))

        lines = [self.output[i:i+28] for i in range(0, min(len(self.output), 84), 28)]
        y     = 82
        for line in lines[:3]:
            surf = self.font.render(line, True, YELLOW if self.output else DIM)
            self.screen.blit(surf, (8, y))
            y   += 14

        if self.status:
            st = self.font.render(self.status, True, GREEN)
            self.screen.blit(st, (8, 160))

        hint = self.font.render("ENTER=run  ESC=back", True, DIM)
        self.screen.blit(hint, (8, 228))
        pygame.display.flip()

    def draw(self):
        if self.mode == "menu":
            self.draw_menu()
        elif self.mode == "input":
            self.draw_input()

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if self.mode == "menu":
                if event.key == pygame.K_DOWN:
                    self.selected = (self.selected + 1) % len(MODES)
                elif event.key == pygame.K_UP:
                    self.selected = (self.selected - 1) % len(MODES)
                elif event.key == pygame.K_RETURN:
                    self.mode   = "input"
                    self.input  = ""
                    self.output = ""
                    self.status = ""
            elif self.mode == "input":
                if event.key == pygame.K_RETURN:
                    self.process()
                elif event.key == pygame.K_BACKSPACE:
                    self.input = self.input[:-1]
                elif event.key == pygame.K_ESCAPE:
                    self.mode  = "menu"
                    self.input = ""
                else:
                    self.input += event.unicode
