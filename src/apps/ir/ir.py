import pygame

BG     = (10, 10, 20)
TEXT   = (255, 255, 255)
ACCENT = (255, 80, 80)

BUTTONS = [
    {"name": "Power",  "code": "0x20DF10EF"},
    {"name": "Vol +",  "code": "0x20DF40BF"},
    {"name": "Vol -",  "code": "0x20DFC03F"},
    {"name": "Ch +",   "code": "0x20DF00FF"},
    {"name": "Ch -",   "code": "0x20DF807F"},
    {"name": "Mute",   "code": "0x20DF906F"},
]

class IRRemote:
    def __init__(self, screen, font):
        self.screen = screen
        self.font   = font

    def send_code(self, code):
        print(f"Sending IR code: {code}")

    def draw(self):
        self.screen.fill(BG)
        title = self.font.render("IR Remote", True, ACCENT)
        self.screen.blit(title, (8, 8))
        pygame.draw.line(self.screen, ACCENT, (0, 24), (240, 24), 1)
        cols, pad = 2, 8
        btn_w = (240 - pad * 3) // cols
        btn_h = 30
        for i, btn in enumerate(BUTTONS):
            col = i % cols
            row = i // cols
            x   = pad + col * (btn_w + pad)
            y   = 32 + pad + row * (btn_h + pad)
            pygame.draw.rect(self.screen, ACCENT, (x, y, btn_w, btn_h), width=1, border_radius=6)
            label = self.font.render(btn["name"], True, TEXT)
            self.screen.blit(label, (x + 10, y + 9))
        pygame.display.flip()

    def handle_input(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            cols, pad = 2, 8
            btn_w = (240 - pad * 3) // cols
            btn_h = 30
            for i, btn in enumerate(BUTTONS):
                col  = i % cols
                row  = i // cols
                x    = pad + col * (btn_w + pad)
                y    = 32 + pad + row * (btn_h + pad)
                rect = pygame.Rect(x, y, btn_w, btn_h)
                if rect.collidepoint(event.pos):
                    self.send_code(btn["code"])
