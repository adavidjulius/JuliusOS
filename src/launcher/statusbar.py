import pygame
import datetime

BG     = (20, 30, 50)
TEXT   = (255, 255, 255)
ACCENT = (0, 200, 255)
GREEN  = (0, 255, 100)
RED    = (255, 80, 80)
YELLOW = (255, 200, 0)

class StatusBar:
    def __init__(self, screen, font):
        self.screen  = screen
        self.font    = font
        self.wifi    = True
        self.bt      = True
        self.battery = 85

    def get_battery_color(self):
        if self.battery > 50: return GREEN
        if self.battery > 20: return YELLOW
        return RED

    def draw_battery(self, x, y):
        pygame.draw.rect(self.screen, TEXT,  (x, y, 20, 10), width=1, border_radius=2)
        pygame.draw.rect(self.screen, TEXT,  (x + 20, y + 3, 2, 4))
        fill  = int((self.battery / 100) * 18)
        color = self.get_battery_color()
        pygame.draw.rect(self.screen, color, (x + 1, y + 1, fill, 8), border_radius=1)

    def draw_wifi(self, x, y):
        color = ACCENT if self.wifi else RED
        pygame.draw.rect(self.screen, color, (x,     y + 6, 3, 4))
        pygame.draw.rect(self.screen, color, (x + 4, y + 3, 3, 7))
        pygame.draw.rect(self.screen, color, (x + 8, y,     3, 10))

    def draw_bt(self, x, y):
        color = ACCENT if self.bt else RED
        label = self.font.render("B", True, color)
        self.screen.blit(label, (x, y))

    def draw(self):
        pygame.draw.rect(self.screen, BG, (0, 0, 240, 28))
        pygame.draw.line(self.screen, ACCENT, (0, 27), (240, 27), 1)
        title = self.font.render("Julius OS", True, ACCENT)
        self.screen.blit(title, (8, 8))
        now  = datetime.datetime.now().strftime("%H:%M")
        time = self.font.render(now, True, TEXT)
        self.screen.blit(time, (95, 8))
        self.draw_wifi(170, 9)
        self.draw_bt(188, 8)
        self.draw_battery(200, 9)
        pct = self.font.render(f"{self.battery}%", True, self.get_battery_color())
        self.screen.blit(pct, (223, 8))
