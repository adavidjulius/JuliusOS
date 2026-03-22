import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from launcher.boot      import boot_screen
from launcher.statusbar import StatusBar
from apps.terminal.terminal               import Terminal
from apps.wifi.wifi                       import WiFiScanner
from apps.ir.ir                           import IRRemote
from apps.bluetooth.bluetooth             import BluetoothScanner
from apps.gpio.gpio                       import GPIOControl
from apps.settings.settings               import Settings
from apps.connect.connect                 import DeviceConnect
from apps.filetransfer.filetransfer       import FileTransfer
from apps.clipboard.clipboard             import Clipboard
from apps.hotspot.hotspot                 import Hotspot
from apps.scanner.scanner                 import PortScanner
from apps.filemanager.filemanager         import FileManager
from apps.sysmon.sysmon                   import SysMon
from apps.ssh.ssh                         import SSHClient
from apps.notes.notes                     import Notes
from apps.nettools.nettools               import NetTools
from apps.packetanalyzer.packetanalyzer   import PacketAnalyzer
from apps.wakeonlan.wakeonlan             import WakeOnLAN
from apps.speedtest.speedtest             import SpeedTest
from apps.calculator.calculator           import Calculator
from apps.todo.todo                       import Todo
from apps.passwords.passwords             import PasswordManager
from apps.weather.weather                 import Weather
from apps.hasher.hasher                   import Hasher
from apps.encoder.encoder                 import Encoder
from apps.netmonitor.netmonitor           import NetMonitor
from apps.texteditor.texteditor           import TextEditor
from apps.timer.timer                     import Timer
from apps.processkiller.processkiller     import ProcessKiller
from apps.netmapper.netmapper             import NetMapper
from apps.sysinfo.sysinfo                 import SysInfo
from apps.firewall.firewall               import Firewall
from apps.logviewer.logviewer             import LogViewer
from apps.usbtools.usbtools               import USBTools

import pygame

WIDTH, HEIGHT = 240, 240
FPS           = 30

BG      = (10, 10, 20)
CARD    = (20, 30, 50)
ACCENT  = (0, 200, 255)
TEXT    = (255, 255, 255)
DIM     = (80, 80, 80)
GREEN   = (0, 255, 100)

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
    {"name": "Packets",   "color": (255, 100, 200)},
    {"name": "WakeOnLAN", "color": (100, 255, 180)},
    {"name": "SpeedTest", "color": (255, 180,  50)},
    {"name": "Calc",      "color": (0,   220, 255)},
    {"name": "Todo",      "color": (100, 255, 100)},
    {"name": "Passwords", "color": (255, 100, 100)},
    {"name": "Weather",   "color": (100, 180, 255)},
    {"name": "Hasher",    "color": (255, 140, 200)},
    {"name": "Encoder",   "color": (140, 255, 140)},
    {"name": "NetMon",    "color": (0,   200, 255)},
    {"name": "Editor",    "color": (200, 200, 100)},
    {"name": "Timer",     "color": (255, 160,  80)},
    {"name": "ProcKill",  "color": (255, 60,   60)},
    {"name": "NetMapper", "color": (60,  200, 255)},
    {"name": "SysInfo",   "color": (180, 180, 255)},
    {"name": "Firewall",  "color": (255, 80,   40)},
    {"name": "Logs",      "color": (200, 255, 200)},
    {"name": "USB",       "color": (255, 200, 100)},
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
    "Packets"   : PacketAnalyzer(screen, font_big),
    "WakeOnLAN" : WakeOnLAN(screen, font_big),
    "SpeedTest" : SpeedTest(screen, font_big),
    "Calc"      : Calculator(screen, font_big),
    "Todo"      : Todo(screen, font_big),
    "Passwords" : PasswordManager(screen, font_big),
    "Weather"   : Weather(screen, font_big),
    "Hasher"    : Hasher(screen, font_big),
    "Encoder"   : Encoder(screen, font_big),
    "NetMon"    : NetMonitor(screen, font_big),
    "Editor"    : TextEditor(screen, font_big),
    "Timer"     : Timer(screen, font_big),
    "ProcKill"  : ProcessKiller(screen, font_big),
    "NetMapper" : NetMapper(screen, font_big),
    "SysInfo"   : SysInfo(screen, font_big),
    "Firewall"  : Firewall(screen, font_big),
    "Logs"      : LogViewer(screen, font_big),
    "USB"       : USBTools(screen, font_big),
    "Settings"  : Settings(screen, font_big),
}

# Gesture state
current_app    = None
scroll_offset  = 0
recent_apps    = []
show_recent    = False

# Touch/drag tracking
drag_start_x   = 0
drag_start_y   = 0
drag_start_time= 0
dragging       = False
drag_start_scroll = 0

COLS         = 2
PAD          = 8
ROWS_VISIBLE = 3

def get_card_dims():
    card_w = (WIDTH - PAD * 3) // COLS
    card_h = (HEIGHT - 28 - PAD * 4) // ROWS_VISIBLE
    return card_w, card_h

def get_max_scroll():
    card_w, card_h = get_card_dims()
    total_rows     = (len(APPS) + 1) // COLS
    return max(0, total_rows * (card_h + PAD) - (HEIGHT - 28))

def open_app(name):
    global current_app, recent_apps, show_recent
    current_app = name
    show_recent = False
    if name in recent_apps:
        recent_apps.remove(name)
    recent_apps.insert(0, name)
    if len(recent_apps) > 6:
        recent_apps = recent_apps[:6]

def draw_gesture_hint():
    # Bottom gesture bar
    pygame.draw.rect(screen, (20, 20, 35), (0, 228, 240, 12))
    pygame.draw.line(screen, DIM, (0, 228), (240, 228), 1)
    # Home indicator line
    pygame.draw.rect(screen, DIM, (85, 232, 70, 3), border_radius=2)

def draw_recent():
    screen.fill(BG)
    title = font_big.render("Recent Apps", True, ACCENT)
    screen.blit(title, (8, 8))
    pygame.draw.line(screen, ACCENT, (0, 24), (240, 24), 1)

    if not recent_apps:
        msg = font_big.render("No recent apps", True, DIM)
        screen.blit(msg, (50, 110))
    else:
        card_w = (WIDTH - PAD * 3) // 2
        card_h = 50
        for i, name in enumerate(recent_apps[:6]):
            col   = i % 2
            row   = i // 2
            x     = PAD + col * (card_w + PAD)
            y     = 32  + row * (card_h + PAD)
            app   = next((a for a in APPS if a["name"] == name), None)
            color = app["color"] if app else ACCENT
            pygame.draw.rect(screen, CARD,  (x, y, card_w, card_h), border_radius=8)
            pygame.draw.rect(screen, color, (x, y, card_w, card_h), width=1, border_radius=8)
            label = font_big.render(name, True, TEXT)
            screen.blit(label, (x + 8, y + card_h // 2 - 6))

    hint = font_small.render("Tap=open  Swipe down=home", True, DIM)
    screen.blit(hint, (8, 228))
    pygame.display.flip()

def draw_launcher():
    screen.fill(BG)
    statusbar.draw()
    card_w, card_h = get_card_dims()
    total_rows     = (len(APPS) + 1) // COLS
    max_scroll     = get_max_scroll()

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

    draw_gesture_hint()
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

def get_tapped_recent(pos):
    card_w = (WIDTH - PAD * 3) // 2
    card_h = 50
    for i, name in enumerate(recent_apps[:6]):
        col = i % 2
        row = i // 2
        x   = PAD + col * (card_w + PAD)
        y   = 32  + row * (card_h + PAD)
        if pygame.Rect(x, y, card_w, card_h).collidepoint(pos):
            return name
    return None

import time

while True:
    current_time = time.time()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        # ── MOUSE DOWN — start drag tracking ──
        if event.type == pygame.MOUSEBUTTONDOWN:
            drag_start_x      = event.pos[0]
            drag_start_y      = event.pos[1]
            drag_start_time   = current_time
            drag_start_scroll = scroll_offset
            dragging          = False

        # ── MOUSE MOVE — detect drag/scroll ──
        if event.type == pygame.MOUSEMOTION:
            if pygame.mouse.get_pressed()[0]:
                dx = event.pos[0] - drag_start_x
                dy = event.pos[1] - drag_start_y
                if abs(dy) > 5 or abs(dx) > 5:
                    dragging = True

                # Scroll launcher vertically
                if current_app is None and not show_recent:
                    new_scroll = drag_start_scroll - dy
                    scroll_offset = max(0, min(new_scroll, get_max_scroll()))

        # ── MOUSE UP — detect gestures and taps ──
        if event.type == pygame.MOUSEBUTTONUP:
            dx       = event.pos[0] - drag_start_x
            dy       = event.pos[1] - drag_start_y
            duration = current_time - drag_start_time
            speed    = abs(dy) / max(duration, 0.001)

            # GESTURE: Swipe UP from bottom → Recent apps
            if drag_start_y > 200 and dy < -40 and speed > 100:
                show_recent = True
                current_app = None

            # GESTURE: Swipe DOWN from top → Go home
            elif drag_start_y < 50 and dy > 40:
                current_app = None
                show_recent = False

            # GESTURE: Swipe RIGHT → Go back / home
            elif dx > 60 and abs(dy) < 40 and current_app:
                current_app = None
                show_recent = False

            # GESTURE: Swipe DOWN anywhere in app → Go home
            elif dy > 80 and abs(dx) < 40 and current_app:
                current_app = None
                show_recent = False

            # GESTURE: Swipe DOWN in recent → Close recent
            elif dy > 40 and show_recent:
                show_recent = False

            # TAP — open app
            elif not dragging or (abs(dx) < 10 and abs(dy) < 10):
                if show_recent:
                    name = get_tapped_recent(event.pos)
                    if name:
                        open_app(name)
                elif current_app is None:
                    name = get_tapped_app(event.pos)
                    if name:
                        open_app(name)

        # Pass keyboard input to current app
        if current_app and event.type == pygame.KEYDOWN:
            app_instances[current_app].handle_input(event)

        if current_app and event.type == pygame.MOUSEBUTTONDOWN:
            app_instances[current_app].handle_input(event)

    # Draw
    if show_recent:
        draw_recent()
    elif current_app:
        try:
            app_instances[current_app].draw()
            draw_gesture_hint()
            pygame.display.flip()
        except Exception as e:
            print(f"App error: {e}")
            current_app = None
    else:
        draw_launcher()

    clock.tick(FPS)
