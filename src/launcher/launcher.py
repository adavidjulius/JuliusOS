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
from apps.connect.connect           import DeviceConnect
from apps.filetransfer.filetransfer import FileTransfer
from apps.clipboard.clipboard       import Clipboard
from apps.hotspot.hotspot           import Hotspot
from apps.scanner.scanner           import PortScanner
from apps.filemanager.filemanager   import FileManager
from apps.sysmon.sysmon             import SysMon
from apps.ssh.ssh                   import SSHClient
from apps.notes.notes               import Notes
from apps.nettools.nettools         import NetTools

WIDTH, HEIGHT = 240, 240
FPS           = 30

BG      = (10, 10, 20)
CARD    = (20, 30, 50)
ACCENT  = (0, 200, 255)
TEXT    = (255, 255, 255)
SUBTEXT = (100, 150, 200)

APPS = [
    {"name": "Terminal",  "color": (0,   180, 120)},
    {"name": "WiFi",      "color": (0,   120, 255)},
    {"name": "IR",        "color": (255, 80,   80)},
    {"name": "Bluetooth", "color": (80,  80,  255)},
    {"name": "GPIO",      "color": (255, 200,   0)},
    {"name": "Connect",   "color": (0,   200, 180)},
    {"name": "Transfer",  "color": (180, 0,   255)},
    {"name": "Clipboard", "color": (255, 140,   0)},
    {"name": "Hotspot",   "color": (255, 60,  120)},
    {"name": "Scanner",   "color": (0,   255, 128)},
    {"name": "Files",     "color": (255, 220,  80)},
    {"name": "SysMon",    "color": (80,  200, 255)},
    {"name": "SSH",       "color": (0,   255, 200)},
    {"name": "Notes",     "color": (255, 255, 100)},
    {"name": "NetTools",  "color": (100, 180, 255)},
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
    "Connect"   : DeviceConnect(screen, font_big),
    "Transfer"  : FileTransfer(screen, font_big),
    "Clipboard" : Clipboard(screen, font_big),
    "Hotspot"   : Hotspot(screen, font_big),
    "Scanner"   : PortScanner(screen, font_big),
    "Files"     : FileManager(screen, font_big),
    "SysMon"    : SysMon(screen, font_big),
    "SSH"       : SSHClient(screen, font_big),
    "Notes"     : Notes(screen, font_big),
    "NetTools"  : NetTools(screen, font_big),
    "Settings"  : Settings(screen, font_big),
}

current_app   = None
scroll_offset = 0
COLS          = 2
PAD           = 8
ROWS_VISIBLE  = 3

def get_card_dims():
    card_w = (WIDTH - PAD * 3) // COLS
    card_h = (HEIGHT - 28 - PAD * 4) // ROWS_VISIBLE
    return card_w, card_h

def draw_launcher():
    screen.fill(BG)
    statusbar.draw()

    card_w, card_h = get_card_dims()
    total_rows     = (len(APPS) + 1) // COLS
    max_scroll     = max(0, total_rows * (card_h + PAD) - (HEIGHT - 28))

    for i, app in enumerate(APPS):
        col = i % COLS
        row = i // COLS
        x   = PAD + col * (card_w + PAD)
        y   = 28 + PAD + row * (card_h + PAD) - scroll_offset

        if y + card_h < 28 or y > HEIGHT:
            continue

        pygame.draw.rect(screen, CARD,        (x, y, card_w, card_h), border_radius=8)
        pygame.draw.rect(screen, app["color"], (x, y, card_w, card_h), width=1, border_radius=8)
        label = font_big.render(app["name"], True, TEXT)
        screen.blit(label, (x + 8, y + card_h // 2 - 6))

    if max_scroll > 0:
        bar_h = int((HEIGHT - 28) * (HEIGHT - 28) / (total_rows * (card_h + PAD)))
        bar_y = 28 + int(scroll_offset / max_scroll * ((HEIGHT - 28) - bar_h))
        pygame.draw.rect(screen, ACCENT, (236, bar_y, 3, bar_h), border_radius=2)

    pygame.display.flip()

def get_tapped_app(pos):
    card_w, card_h = get_card_dims()
    for i, app in enumerate(APPS):
        col = i % COLS
        row = i // COLS
        x   = PAD + col * (card_w + PAD)
        y   = 28 + PAD + row * (card_h + PAD) - scroll_offset
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
            if current_app is None:
                card_w, card_h = get_card_dims()
                total_rows     = (len(APPS) + 1) // COLS
                max_scroll     = max(0, total_rows * (card_h + PAD) - (HEIGHT - 28))
                if event.key == pygame.K_DOWN:
                    scroll_offset = min(scroll_offset + card_h + PAD, max_scroll)
                if event.key == pygame.K_UP:
                    scroll_offset = max(scroll_offset - card_h - PAD, 0)

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
```

---

## ✅ Julius OS v0.3 Complete
```
SSH Client     ✅  connect to devices via SSH
Notes          ✅  create read edit delete notes
Net Tools      ✅  ping traceroute DNS lookup
Launcher       ✅  16 apps total smooth scroll
```

Commit with:
```
🚀 Julius OS v0.3 — SSH, Notes, NetTools added
