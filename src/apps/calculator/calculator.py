import pygame

BG     = (10, 10, 20)
TEXT   = (255, 255, 255)
ACCENT = (0, 200, 255)
GREEN  = (0, 255, 100)
DIM    = (80, 80,   80)
RED    = (255, 80,  80)

BUTTONS = [
    ["C", "+/-", "%", "/"],
    ["7", "8",   "9", "*"],
    ["4", "5",   "6", "-"],
    ["1", "2",   "3", "+"],
]

class Calculator:
    def __init__(self, screen, font):
        self.screen  = screen
        self.font    = font
        self.display = "0"
        self.prev    = ""
        self.op      = ""
        self.reset   = False

    def press(self, btn):
        if btn == "C":
            self.display = "0"
            self.prev    = ""
            self.op      = ""
            self.reset   = False
            self.display = self.display[:-1] or "0"
        elif btn == "+/-":
            if self.display != "0":
                self.display = str(-float(self.display))
                if self.display.endswith(".0"):
                    self.display = self.display[:-2]
        elif btn == "%":
            try:
                self.display = str(float(self.display) / 100)
                if self.display.endswith(".0"):
                    self.display = self.display[:-2]
            except:
                self.display = "Error"
        elif btn in ["/", "*", "-", "+"]:
            self.prev  = self.display
            self.op    = btn
            self.reset = True
        elif btn == "=":
            try:
                a      = float(self.prev)
                b      = float(self.display)
                result = {
                    "+" : a + b,
                    "-" : a - b,
                    "*" : a * b,
                    "/" : a / b if b != 0 else None
                }.get(self.op)
                if result is None:
                    self.display = "Error"
                else:
                    self.display = str(result)
                    if self.display.endswith(".0"):
                        self.display = self.display[:-2]
            except:
                self.display = "Error"
            self.prev  = ""
            self.op    = ""
            self.reset = False
        elif btn == ".":
            if self.reset:
                self.display = "0."
                self.reset   = False
            elif "." not in self.display:
                self.display += "."
        else:
            if self.display == "0" or self.reset:
                self.display = btn
                self.reset   = False
            else:
                self.display += btn

    def draw(self):
        self.screen.fill(BG)
        title = self.font.render("Calculator", True, ACCENT)
        self.screen.blit(title, (8, 8))
        pygame.draw.line(self.screen, ACCENT, (0, 24), (240, 24), 1)

        # Display
        pygame.draw.rect(self.screen, (20, 30, 50), (8, 28, 224, 30), border_radius=6)
        disp = self.font.render(self.display[-20:], True, GREEN)
        self.screen.blit(disp, (220 - disp.get_width(), 36))

        # Expression
        if self.prev and self.op:
            expr = self.font.render(f"{self.prev} {self.op}", True, DIM)
            self.screen.blit(expr, (12, 30))

        # Buttons
        pad   = 6
        btn_w = (240 - pad * 5) // 4
        btn_h = 28

        for row_i, row in enumerate(BUTTONS):
            for col_i, btn in enumerate(row):
                x = pad + col_i * (btn_w + pad)
                y = 64 + row_i * (btn_h + pad)

                if btn in ["/", "*", "-", "+", "="]:
                    color = ACCENT
                elif btn in ["C", "+/-", "%"]:
                    color = (80, 80, 120)
                    color = RED
                else:
                    color = (20, 30, 50)

                pygame.draw.rect(self.screen, color,  (x, y, btn_w, btn_h), border_radius=6)
                pygame.draw.rect(self.screen, DIM,    (x, y, btn_w, btn_h), width=1, border_radius=6)
                label = self.font.render(btn, True, TEXT)
                self.screen.blit(label, (
                    x + btn_w // 2 - label.get_width()  // 2,
                    y + btn_h // 2 - label.get_height() // 2
                ))

        pygame.display.flip()

    def handle_input(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            pad   = 6
            btn_w = (240 - pad * 5) // 4
            btn_h = 28
            for row_i, row in enumerate(BUTTONS):
                for col_i, btn in enumerate(row):
                    x    = pad + col_i * (btn_w + pad)
                    y    = 64  + row_i * (btn_h + pad)
                    rect = pygame.Rect(x, y, btn_w, btn_h)
                    if rect.collidepoint(event.pos):
                        self.press(btn)
        if event.type == pygame.KEYDOWN:
            key_map = {
                pygame.K_0: "0", pygame.K_1: "1",
                pygame.K_2: "2", pygame.K_3: "3",
                pygame.K_4: "4", pygame.K_5: "5",
                pygame.K_6: "6", pygame.K_7: "7",
                pygame.K_8: "8", pygame.K_9: "9",
                pygame.K_PLUS     : "+",
                pygame.K_MINUS    : "-",
                pygame.K_ASTERISK : "*",
                pygame.K_SLASH    : "/",
                pygame.K_RETURN   : "=",
                pygame.K_PERIOD   : ".",
            }
            if event.key in key_map:
                self.press(key_map[event.key])
