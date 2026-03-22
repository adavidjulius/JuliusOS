import pygame

BG      = (10, 10, 20)
TEXT    = (255, 255, 255)
ACCENT  = (255, 200, 0)
ON_COL  = (0, 255, 100)
OFF_COL = (80, 80, 80)

PINS = [
    {"pin": 1, "name": "PIN 1", "state": False},
    {"pin": 2, "name": "PIN 2", "state": False},
    {"pin": 3, "name": "PIN 3", "state": False},
    {"pin": 4, "name": "PIN 4", "state": False},
    {"pin": 5, "name": "PIN 5", "state": False},
    {"pin": 6, "name": "PIN 6", "state": False},
]

class GPIOControl:
    def __init__(self, screen, font):
        self.screen = screen
        self.font   = font
        self.pins   = PINS

    def toggle_pin(self, index):
        self.pins[index]["state"] = not self.pins[index]["state"]
        state = self.pins[index]["state"]
        pin   = self.pins[index]["pin"]
        print(f"PIN {pin} → {'HIGH' if state else 'LOW'}")

    def draw(self):
        self.screen.fill(BG)
        title = self.font.render("GPIO Control", True, ACCENT)
        self.screen.blit(title, (8, 8))
        pygame.draw.line(self.screen, ACCENT, (0, 24), (240, 24), 1)
        cols, pad = 2, 8
        btn_w = (240 - pad * 3) // cols
        btn_h = 30
        for i, pin in enumerate(self.pins):
            col   = i % cols
            row   = i // cols
            x     = pad + col * (btn_w + pad)
            y     = 32 + pad + row * (btn_h + pad)
            color = ON_COL if pin["state"] else OFF_COL
            pygame.draw.rect(self.screen, color, (x, y, btn_w, btn_h), border_radius=6)
            label = self.font.render(
                f"{pin['name']} {'ON' if pin['state'] else 'OFF'}", True, TEXT
            )
            self.screen.blit(label, (x + 8, y + 9))
        pygame.display.flip()

    def handle_input(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            cols, pad = 2, 8
            btn_w = (240 - pad * 3) // cols
            btn_h = 30
            for i in range(len(self.pins)):
                col = i % cols
                row = i // cols
                x   = pad + col * (btn_w + pad)
                y   = 32 + pad + row * (btn_h + pad)
                if pygame.Rect(x, y, btn_w, btn_h).collidepoint(event.pos):
                    self.toggle_pin(i)
