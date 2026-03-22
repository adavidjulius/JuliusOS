import pygame
import sys
import os
import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from launcher.boot                  import boot_screen
from launcher.statusbar             import StatusBar
from apps.terminal.terminal         import Terminal
from apps.wifi.wifi                 import WiFiScanner
from apps.ir.ir                     import IRRemote
from apps.bluetooth.bluetooth       import BluetoothScanner
from apps.gpio.gpio                 import GPIOControl
from apps.settings.settings         import Settings

WIDTH, HEIGHT = 240, 240
FPS           = 30

BG      = (10, 10, 20)
CARD    = (20, 30, 50)
ACCENT  = (0, 200, 255)
TEXT    = (255, 255, 255)
SUBTEXT = (100, 150, 200)

APPS = [
    {"name": "Terminal",  "color": (0, 180, 120)},
    {"name": "WiFi",      "color": (0, 120, 255)},
    {"name": "IR",        "color": (255, 80, 80)},
    {"name": "Bluetooth", "color": (80, 80, 255)},
    {"name": "GPIO",      "color": (255, 200, 0)},
    {"name": "Settings",  "color": (150, 150, 150)},
]

pygame.init()
screen     = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Julius OS")
clock      = pygame.time.Clock()
font_big   = pygame.font.SysFont("monospace", 11, bold=True)
font_small = pygame.font.SysFont("monospace", 9)

boot_screen(screen)

statusbar = StatusBar(screen, font_small)

app_instances = {
    "Terminal"  : Terminal(screen, font_big),
    "WiFi"      : WiFiScanner(screen, font_big),
    "IR"        : IRRemote(screen, font_big),
    "Bluetooth" : BluetoothScanner(screen, font_big),
    "GPIO"      : GPIOControl(screen, font_big),
    "Settings"  : Settings(screen, font_big),
}

current_app = None

def draw_launcher():
    screen.fill(BG)
    statusbar.draw()

    cols   = 2
    pad    = 8
    card_w = (WIDTH - pad * 3) // cols
    card_h = (HEIGHT - 28 - pad * 4) // 3

    for i, app in enumerate(APPS):
        col = i % cols
        row = i // cols
        x   = pad + col * (card_w + pad)
        y   = 28 + pad + row * (card_h + pad)
        pygame.draw.rect(screen, CARD,       (x, y, card_w, card_h), border_radius=8)
        pygame.draw.rect(screen, app["color"],(x, y, card_w, card_h), width=1, border_radius=8)
        label = font_big.render(app["name"], True, TEXT)
        screen.blit(label, (x + 8, y + card_h // 2 - 6))

    pygame.display.flip()

def get_tapped_app(pos):
    cols   = 2
    pad    = 8
    card_w = (WIDTH - pad * 3) // cols
    card_h = (HEIGHT - 28 - pad * 4) // 3

    for i, app in enumerate(APPS):
        col = i % cols
        row = i // cols
        x   = pad + col * (card_w + pad)
        y   = 28 + pad + row * (card_h + pad)
        if pygame.Rect(x, y, card_w, card_h).collidepoint(pos):
            return app["name"]
    return None

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                current_app = None
        if event.type == pygame.MOUSEBUTTONDOWN and current_app is None:
            name = get_tapped_app(event.pos)
            if name:
                current_app = name
        if current_app:
            app_instances[current_app].handle_input(event)

    if current_app:
        app_instances[current_app].draw()
    else:
        draw_launcher()

    clock.tick(FPS)
