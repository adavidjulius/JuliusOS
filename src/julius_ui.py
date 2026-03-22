import pygame
import sys
import os
import datetime
import math

sys.path.insert(0, os.path.dirname(__file__))

from launcher.boot                        import boot_screen
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

W, H   = 320, 480
FPS    = 60

BG     = (10, 10, 20)
CARD   = (28, 28, 30)
WHITE  = (255, 255, 255)
DIM    = (120, 120, 130)
DOCK   = (28, 28, 32)
GREEN  = (48, 209, 88)

APPS = [
    {"name":"Terminal",  "bg":(0,61,31),    "ac":(0,255,148),   "page":0},
    {"name":"WiFi",      "bg":(0,31,77),    "ac":(64,156,255),  "page":0},
    {"name":"IR",        "bg":(77,0,0),     "ac":(255,105,97),  "page":0},
    {"name":"Bluetooth", "bg":(26,0,80),    "ac":(191,90,242),  "page":0},
    {"name":"GPIO",      "bg":(77,51,0),    "ac":(255,214,10),  "page":0},
    {"name":"Connect",   "bg":(0,61,53),    "ac":(99,230,190),  "page":0},
    {"name":"Transfer",  "bg":(45,0,80),    "ac":(218,143,255), "page":0},
    {"name":"Scanner",   "bg":(0,51,34),    "ac":(48,209,88),   "page":0},
    {"name":"Files",     "bg":(26,51,0),    "ac":(168,255,120), "page":0},
    {"name":"SysMon",    "bg":(0,51,68),    "ac":(100,210,255), "page":0},
    {"name":"SSH",       "bg":(51,34,0),    "ac":(255,159,10),  "page":0},
    {"name":"Notes",     "bg":(51,45,0),    "ac":(255,224,102), "page":0},
    {"name":"NetTools",  "bg":(0,26,68),    "ac":(90,200,250),  "page":0},
    {"name":"Packets",   "bg":(68,0,51),    "ac":(255,45,120),  "page":0},
    {"name":"Clipboard", "bg":(26,34,0),    "ac":(200,255,120), "page":0},
    {"name":"Hotspot",   "bg":(68,0,17),    "ac":(255,107,107), "page":0},
    {"name":"Calc",      "bg":(0,26,26),    "ac":(0,229,255),   "page":1},
    {"name":"Todo",      "bg":(0,51,0),     "ac":(105,255,71),  "page":1},
    {"name":"Passwords", "bg":(51,0,17),    "ac":(255,92,138),  "page":1},
    {"name":"Weather",   "bg":(0,17,51),    "ac":(116,185,255), "page":1},
    {"name":"Hasher",    "bg":(26,0,51),    "ac":(224,64,251),  "page":1},
    {"name":"Encoder",   "bg":(0,51,0),     "ac":(0,230,118),   "page":1},
    {"name":"NetMon",    "bg":(0,17,51),    "ac":(64,196,255),  "page":1},
    {"name":"Editor",    "bg":(45,34,0),    "ac":(255,215,64),  "page":1},
    {"name":"Timer",     "bg":(51,17,0),    "ac":(255,109,0),   "page":1},
    {"name":"WakeOnLAN", "bg":(0,51,34),    "ac":(105,255,218), "page":1},
    {"name":"SpeedTest", "bg":(0,26,0),     "ac":(118,255,3),   "page":1},
    {"name":"ProcKill",  "bg":(51,0,0),     "ac":(255,23,68),   "page":1},
    {"name":"NetMapper", "bg":(0,17,51),    "ac":(68,138,255),  "page":1},
    {"name":"SysInfo",   "bg":(26,0,26),    "ac":(234,128,252), "page":1},
    {"name":"Firewall",  "bg":(51,10,0),    "ac":(255,110,64),  "page":1},
    {"name":"Logs",      "bg":(0,26,0),     "ac":(185,246,202), "page":1},
    {"name":"USB",       "bg":(26,17,0),    "ac":(255,229,127), "page":1},
    {"name":"Settings",  "bg":(28,28,30),   "ac":(142,142,147), "page":1},
]

DOCK_NAMES = ["Terminal","WiFi","SysMon","Settings"]

pygame.init()
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Julius OS")
clock  = pygame.time.Clock()

font_time   = pygame.font.SysFont("helvetica", 52, bold=False)
font_date   = pygame.font.SysFont("helvetica", 14)
font_status = pygame.font.SysFont("helvetica", 13, bold=True)
font_app    = pygame.font.SysFont("helvetica", 10)
font_title  = pygame.font.SysFont("helvetica", 18, bold=True)
font_small  = pygame.font.SysFont("helvetica", 11)

app_instances = {
    "Terminal"  : Terminal(screen, font_small),
    "WiFi"      : WiFiScanner(screen, font_small),
    "IR"        : IRRemote(screen, font_small),
    "Bluetooth" : BluetoothScanner(screen, font_small),
    "GPIO"      : GPIOControl(screen, font_small),
    "Connect"   : DeviceConnect(screen, font_small),
    "Transfer"  : FileTransfer(screen, font_small),
    "Clipboard" : Clipboard(screen, font_small),
    "Hotspot"   : Hotspot(screen, font_small),
    "Scanner"   : PortScanner(screen, font_small),
    "Files"     : FileManager(screen, font_small),
    "SysMon"    : SysMon(screen, font_small),
    "SSH"       : SSHClient(screen, font_small),
    "Notes"     : Notes(screen, font_small),
    "NetTools"  : NetTools(screen, font_small),
    "Packets"   : PacketAnalyzer(screen, font_small),
    "WakeOnLAN" : WakeOnLAN(screen, font_small),
    "SpeedTest" : SpeedTest(screen, font_small),
    "Calc"      : Calculator(screen, font_small),
    "Todo"      : Todo(screen, font_small),
    "Passwords" : PasswordManager(screen, font_small),
    "Weather"   : Weather(screen, font_small),
    "Hasher"    : Hasher(screen, font_small),
    "Encoder"   : Encoder(screen, font_small),
    "NetMon"    : NetMonitor(screen, font_small),
    "Editor"    : TextEditor(screen, font_small),
    "Timer"     : Timer(screen, font_small),
    "ProcKill"  : ProcessKiller(screen, font_small),
    "NetMapper" : NetMapper(screen, font_small),
    "SysInfo"   : SysInfo(screen, font_small),
    "Firewall"  : Firewall(screen, font_small),
    "Logs"      : LogViewer(screen, font_small),
    "USB"       : USBTools(screen, font_small),
    "Settings"  : Settings(screen, font_small),
}

current_app  = None
current_page = 0
recent_apps  = []
touch_start  = None
touch_start_time = 0

def draw_rounded_rect(surf, color, rect, radius):
    x, y, w, h = rect
    pygame.draw.rect(surf, color, (x+radius, y, w-2*radius, h))
    pygame.draw.rect(surf, color, (x, y+radius, w, h-2*radius))
    pygame.draw.circle(surf, color, (x+radius, y+radius), radius)
    pygame.draw.circle(surf, color, (x+w-radius, y+radius), radius)
    pygame.draw.circle(surf, color, (x+radius, y+h-radius), radius)
    pygame.draw.circle(surf, color, (x+w-radius, y+h-radius), radius)

def draw_icon(surf, app, x, y, size=56):
    r = size // 7
    draw_rounded_rect(surf, app["bg"], (x, y, size, size), r)
    ac = app["ac"]
    name = app["name"]

    cx, cy = x + size//2, y + size//2

    if name == "Terminal":
        pts = [(x+10,cy-4),(cx-2,cy),(x+10,cy+4)]
        pygame.draw.lines(surf, ac, False, pts, 2)
        pygame.draw.line(surf, ac, (cx+2,cy+4),(x+size-10,cy+4), 2)
    elif name == "WiFi":
        for i, (rad, op) in enumerate([(14,80),(10,140),(6,200)]):
            s = pygame.Surface((size,size), pygame.SRCALPHA)
            pygame.draw.arc(s, (*ac, 255-op), (cx-x-rad, cy-y-rad//2, rad*2, rad), 0, math.pi, 2)
            surf.blit(s, (x,y))
        pygame.draw.circle(surf, ac, (cx, cy+4), 2)
    elif name == "IR":
        pygame.draw.circle(surf, ac, (cx, cy), 5)
        for angle in [0, 90, 180, 270]:
            r2 = math.radians(angle)
            x2 = cx + int(math.cos(r2)*12)
            y2 = cy + int(math.sin(r2)*12)
            pygame.draw.line(surf, (*ac, 120), (cx+int(math.cos(r2)*6), cy+int(math.sin(r2)*6)), (x2,y2), 2)
    elif name == "Bluetooth":
        pts = [(cx-5,cy-8),(cx+5,cy-3),(cx,cy),(cx+5,cy+3),(cx-5,cy+8),(cx-5,cy-8)]
        pygame.draw.lines(surf, ac, False, pts, 2)
    elif name == "GPIO":
        pygame.draw.rect(surf, ac, (cx-8,cy-8,16,16), 2)
        for dy2 in [-4,4]:
            pygame.draw.circle(surf, ac, (cx-12, cy+dy2), 2)
            pygame.draw.circle(surf, ac, (cx+12, cy+dy2), 2)
            pygame.draw.line(surf, ac, (cx-8,cy+dy2),(cx-12,cy+dy2), 1)
            pygame.draw.line(surf, ac, (cx+8,cy+dy2),(cx+12,cy+dy2), 1)
    elif name in ["Connect","NetMapper","NetMon"]:
        pygame.draw.circle(surf, ac, (cx-10,cy), 4, 2)
        pygame.draw.circle(surf, ac, (cx+8,cy-8), 3, 2)
        pygame.draw.circle(surf, ac, (cx+8,cy+8), 3, 2)
        pygame.draw.line(surf, (*ac,150), (cx-6,cy),(cx+5,cy-6), 1)
        pygame.draw.line(surf, (*ac,150), (cx-6,cy),(cx+5,cy+6), 1)
    elif name == "Transfer":
        pygame.draw.line(surf, ac, (x+8,cy-4),(x+size-8,cy-4), 2)
        pts1 = [(x+size-12,cy-8),(x+size-8,cy-4),(x+size-12,cy)]
        pygame.draw.lines(surf, ac, False, pts1, 2)
        pygame.draw.line(surf, (*ac,150), (x+8,cy+4),(x+size-8,cy+4), 2)
        pts2 = [(x+12,cy),(x+8,cy+4),(x+12,cy+8)]
        pygame.draw.lines(surf, (*ac,150), False, pts2, 2)
    elif name == "Scanner":
        pygame.draw.circle(surf, ac, (cx-2,cy-2), 8, 2)
        pygame.draw.line(surf, ac, (cx+4,cy+4),(cx+10,cy+10), 2)
        pygame.draw.line(surf, (*ac,150), (cx-6,cy-2),(cx+2,cy-2), 1)
        pygame.draw.line(surf, (*ac,150), (cx-2,cy-6),(cx-2,cy+2), 1)
    elif name == "Files":
        pts = [(x+8,y+8),(x+size-8,y+8),(x+size-8,y+size-8),(x+8,y+size-8)]
        pygame.draw.polygon(surf, ac, pts, 2)
        pygame.draw.line(surf, (*ac,180), (cx-8,cy-2),(cx+8,cy-2), 2)
        pygame.draw.line(surf, (*ac,120), (cx-8,cy+2),(cx+6,cy+2), 2)
        pygame.draw.line(surf, (*ac,80), (cx-8,cy+6),(cx+4,cy+6), 2)
    elif name == "SysMon":
        pts = [(x+4,cy+4),(x+10,cy-4),(x+16,cy+2),(cx,cy-8),(cx+8,cy),(cx+14,cy-4),(x+size-4,cy+2)]
        pygame.draw.lines(surf, ac, False, pts, 2)
    elif name == "SSH":
        pygame.draw.rect(surf, ac, (x+6,y+10,size-12,size-20), 2, border_radius=3)
        t = font_small.render("SSH", True, ac)
        surf.blit(t, (cx-t.get_width()//2, cy-t.get_height()//2))
    elif name == "Notes":
        pts = [(x+8,y+8),(x+size-8,y+8),(x+size-8,y+size-10),(x+size-14,y+size-8),(x+8,y+size-8)]
        pygame.draw.polygon(surf, ac, pts, 2)
        for i, ly in enumerate([cy-8,cy-3,cy+2,cy+7]):
            op = 255 - i*50
            pygame.draw.line(surf, (*ac,op), (x+12,ly),(x+size-12,ly), 1)
    elif name == "Passwords":
        pygame.draw.rect(surf, ac, (cx-9,cy-2,18,12), 2, border_radius=3)
        pygame.draw.arc(surf, ac, (cx-7,cy-12,14,14), 0, math.pi, 2)
        pygame.draw.circle(surf, ac, (cx,cy+3), 3)
    elif name == "Calc":
        pygame.draw.rect(surf, ac, (x+8,y+8,size-16,size-16), 2, border_radius=4)
        pygame.draw.rect(surf, (*ac,80), (x+10,y+10,size-20,10))
        for r in range(3):
            for c2 in range(3):
                pygame.draw.circle(surf, ac, (x+14+c2*8, cy+2+r*7), 2)
    elif name == "Todo":
        for i, (ly, op) in enumerate([(cy-8,255),(cy-1,180),(cy+6,100)]):
            pygame.draw.line(surf, (*ac,op), (x+10,ly),(x+16,ly+5), 2)
            pygame.draw.line(surf, (*ac,op), (x+16,ly+5),(x+22,ly-2), 2)
            pygame.draw.line(surf, (*ac,op//2), (x+24,ly),(x+size-10,ly), 2)
    elif name == "Weather":
        pygame.draw.circle(surf, ac, (cx-4,cy-2), 7, 2)
        pygame.draw.arc(surf, ac, (cx-2,cy-8,16,14), math.pi*0.8, math.pi*2, 2)
        for i, rx in enumerate([cx-8,cx-2,cx+4]):
            pygame.draw.line(surf, (*ac,150-i*40), (rx,cy+7),(rx-2,cy+13), 2)
    elif name == "Hasher":
        pygame.draw.line(surf, ac, (cx-6,cy-10),(cx-8,cy+10), 2)
        pygame.draw.line(surf, ac, (cx+2,cy-10),(cx,cy+10), 2)
        pygame.draw.line(surf, (*ac,180), (cx-10,cy-3),(cx+6,cy-3), 2)
        pygame.draw.line(surf, (*ac,180), (cx-11,cy+4),(cx+5,cy+4), 2)
    elif name == "Encoder":
        pygame.draw.rect(surf, ac, (x+6,y+12,12,14), 2, border_radius=2)
        pygame.draw.rect(surf, ac, (x+size-18,y+12,12,14), 2, border_radius=2)
        pygame.draw.line(surf, ac, (x+18,cy-2),(x+size-18,cy-2), 2)
        pygame.draw.line(surf, (*ac,150), (x+18,cy+3),(x+size-18,cy+3), 1)
    elif name == "Timer":
        pygame.draw.circle(surf, ac, (cx,cy+2), 10, 2)
        pygame.draw.line(surf, ac, (cx,cy+2),(cx,cy-4), 2)
        pygame.draw.line(surf, ac, (cx,cy+2),(cx+5,cy+5), 2)
        pygame.draw.line(surf, (*ac,150), (cx-5,y+8),(cx+5,y+8), 2)
    elif name == "Editor":
        pts = [(cx+8,cy-10),(cx-8,cy+8),(cx-10,cy+10),(cx-8,cy+8)]
        pygame.draw.lines(surf, ac, False, pts, 2)
        pygame.draw.line(surf, (*ac,100), (cx-10,cy+12),(cx+4,cy+12), 1)
    elif name == "Firewall":
        pts2 = [(cx,y+6),(x+size-8,cy-6),(x+size-8,cy+4),(cx,y+size-6),(x+8,cy+4),(x+8,cy-6),(cx,y+6)]
        pygame.draw.polygon(surf, ac, pts2, 2)
        pygame.draw.line(surf, ac, (cx,cy-5),(cx,cy+5), 2)
    elif name == "Logs":
        pygame.draw.rect(surf, ac, (x+8,y+8,size-16,size-16), 2, border_radius=3)
        for i, ly in enumerate([cy-8,cy-3,cy+2,cy+7]):
            pygame.draw.line(surf, (*ac,220-i*50), (x+12,ly),(x+size-12,ly), 2)
    elif name == "USB":
        pygame.draw.line(surf, ac, (cx,y+8),(cx,y+size-10), 2)
        pts3 = [(cx-6,y+12),(cx,y+8),(cx+6,y+12)]
        pygame.draw.lines(surf, ac, False, pts3, 2)
        pygame.draw.rect(surf, ac, (cx-5,cy-6,10,6), 2)
        pygame.draw.rect(surf, ac, (cx-5,cy+2,10,6), 2)
        pygame.draw.circle(surf, ac, (cx,y+size-10), 4, 2)
    elif name == "Settings":
        pygame.draw.circle(surf, ac, (cx,cy), 5, 2)
        for ang in range(0, 360, 45):
            r2 = math.radians(ang)
            x1 = cx + int(math.cos(r2)*8)
            y1 = cy + int(math.sin(r2)*8)
            x2 = cx + int(math.cos(r2)*12)
            y2 = cy + int(math.sin(r2)*12)
            pygame.draw.line(surf, ac, (x1,y1),(x2,y2), 2)
    elif name in ["WakeOnLAN","Hotspot","SpeedTest","Clipboard","NetTools","ProcKill","SysInfo"]:
        icons_map = {
            "WakeOnLAN": lambda: [
                pygame.draw.rect(surf, ac, (x+8,y+12,size-16,size-24), 2, border_radius=3),
                [pygame.draw.line(surf, ac, (x+12+i*6,cy-2),(x+14+i*6,cy+4), 2) for i in range(4)]
            ],
            "Hotspot": lambda: [
                pygame.draw.arc(surf, ac, (x+4,y+8,size-8,size-8), math.pi*0.1, math.pi*0.9, 2),
                pygame.draw.circle(surf, ac, (cx,cy+4), 3),
                pygame.draw.line(surf, (*ac,150), (cx,cy+7),(cx,cy+12), 2)
            ],
            "SpeedTest": lambda: [
                pygame.draw.arc(surf, ac, (x+6,y+10,size-12,size-12), math.pi, 0, 3),
                pygame.draw.line(surf, ac, (cx,cy),(cx+8,cy-8), 2),
                pygame.draw.circle(surf, ac, (cx,cy), 3)
            ],
            "Clipboard": lambda: [
                pygame.draw.rect(surf, ac, (x+8,y+10,size-16,size-18), 2, border_radius=3),
                pygame.draw.rect(surf, ac, (cx-6,y+7,12,6), 2, border_radius=2),
                [pygame.draw.line(surf, (*ac,200-i*60), (x+12,cy-5+i*6),(x+size-12,cy-5+i*6), 1) for i in range(3)]
            ],
            "NetTools": lambda: [
                pygame.draw.rect(surf, ac, (cx-8,y+8,10,8), 2),
                pygame.draw.rect(surf, ac, (x+8,cy,10,8), 2),
                pygame.draw.rect(surf, ac, (x+size-18,cy,10,8), 2),
                pygame.draw.line(surf, ac, (cx-3,y+16),(cx-3,cy), 1),
                pygame.draw.line(surf, ac, (cx-3,cy+4),(x+18,cy+4), 1),
                pygame.draw.line(surf, ac, (cx-3,cy+4),(x+size-13,cy+4), 1)
            ],
            "ProcKill": lambda: [
                pygame.draw.rect(surf, ac, (x+6,y+10,size-12,size-20), 2, border_radius=3),
                pygame.draw.line(surf, ac, (cx-7,cy-5),(cx+7,cy+5), 2),
                pygame.draw.line(surf, ac, (cx+7,cy-5),(cx-7,cy+5), 2)
            ],
            "SysInfo": lambda: [
                pygame.draw.circle(surf, ac, (cx,cy), 12, 2),
                pygame.draw.line(surf, ac, (cx,cy-2),(cx,cy+7), 3),
                pygame.draw.circle(surf, ac, (cx,cy-6), 2)
            ],
        }
        icons_map[name]()
    else:
        t = font_app.render(name[:4], True, ac)
        surf.blit(t, (cx-t.get_width()//2, cy-t.get_height()//2))

def draw_status_bar():
    now = datetime.datetime.now()
    t   = now.strftime("%H:%M")
    ts  = font_status.render(t, True, WHITE)
    screen.blit(ts, (16, 12))
    bat_x = W - 50
    pygame.draw.rect(screen, WHITE, (bat_x, 12, 28, 13), 1, border_radius=3)
    pygame.draw.rect(screen, WHITE, (bat_x+28, 15, 3, 7), border_radius=1)
    pygame.draw.rect(screen, GREEN, (bat_x+2, 14, 22, 9), border_radius=2)
    for i in range(3):
        bar_x = W - 95 + i*7
        h2    = 6 + i*2
        pygame.draw.rect(screen, (*WHITE, 80+i*60), (bar_x, 20-h2//2, 5, h2), border_radius=1)

def draw_home():
    screen.fill(BG)
    draw_status_bar()
    now  = datetime.datetime.now()
    time_str = now.strftime("%H:%M")
    date_str = now.strftime("%A, %B %d")
    ts   = font_time.render(time_str, True, WHITE)
    ds   = font_date.render(date_str, True, (*WHITE, 180))
    screen.blit(ts, (W//2 - ts.get_width()//2, 38))
    screen.blit(ds, (W//2 - ds.get_width()//2, 98))

    page_apps = [a for a in APPS if a["page"] == current_page]
    cols, pad = 4, 10
    icon_size = (W - pad*(cols+1)) // cols
    rows      = (len(page_apps) + cols - 1) // cols
    start_y   = 126

    for i, app in enumerate(page_apps):
        col = i % cols
        row = i // cols
        ix  = pad + col*(icon_size+pad)
        iy  = start_y + row*(icon_size+22+6)
        draw_icon(screen, app, ix, iy, icon_size)
        label = font_app.render(app["name"], True, (*WHITE, 200))
        screen.blit(label, (ix + icon_size//2 - label.get_width()//2, iy+icon_size+3))

    dot_y = H - 78
    for i in range(2):
        color = WHITE if i == current_page else (*WHITE, 80)
        pygame.draw.circle(screen, color, (W//2 - 6 + i*12, dot_y), 4 if i==current_page else 3)

    dock_y = H - 70
    pygame.draw.rect(screen, DOCK, (14, dock_y, W-28, 60), border_radius=18)
    dock_apps  = [a for a in APPS if a["name"] in DOCK_NAMES]
    dock_size  = 48
    dock_pad   = (W-28 - len(dock_apps)*dock_size) // (len(dock_apps)+1)
    for i, app in enumerate(dock_apps):
        dx = 14 + dock_pad*(i+1) + dock_size*i
        draw_icon(screen, app, dx, dock_y+6, dock_size)

    bar_x = W//2 - 50
    pygame.draw.rect(screen, (*WHITE, 100), (bar_x, H-8, 100, 4), border_radius=2)

def draw_app_screen():
    app = next((a for a in APPS if a["name"] == current_app), None)
    if not app:
        return
    screen.fill(BG)
    draw_status_bar()
    pygame.draw.line(screen, (40,40,50), (0,36), (W,36), 1)
    title = font_title.render(current_app, True, WHITE)
    screen.blit(title, (W//2 - title.get_width()//2, 42))
    try:
        app_instances[current_app].draw()
    except Exception as e:
        err = font_small.render(f"Error: {str(e)[:30]}", True, (255,80,80))
        screen.blit(err, (10, H//2))
    bar_x = W//2 - 50
    pygame.draw.rect(screen, (*WHITE, 100), (bar_x, H-8, 100, 4), border_radius=2)

def get_tapped_app(pos):
    page_apps = [a for a in APPS if a["page"] == current_page]
    cols, pad = 4, 10
    icon_size = (W - pad*(cols+1)) // cols
    start_y   = 126
    for i, app in enumerate(page_apps):
        col = i % cols
        row = i // cols
        ix  = pad + col*(icon_size+pad)
        iy  = start_y + row*(icon_size+22+6)
        if ix <= pos[0] <= ix+icon_size and iy <= pos[1] <= iy+icon_size:
            return app["name"]
    dock_y    = H - 70
    dock_apps = [a for a in APPS if a["name"] in DOCK_NAMES]
    dock_size = 48
    dock_pad  = (W-28 - len(dock_apps)*dock_size) // (len(dock_apps)+1)
    for i, app in enumerate(dock_apps):
        dx = 14 + dock_pad*(i+1) + dock_size*i
        if dx <= pos[0] <= dx+dock_size and dock_y+6 <= pos[1] <= dock_y+54:
            return app["name"]
    return None

import time as time_mod
touch_start_time = 0

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if event.type == pygame.MOUSEBUTTONDOWN:
            touch_start      = event.pos
            touch_start_time = time_mod.time()

        if event.type == pygame.MOUSEBUTTONUP:
            if touch_start is None:
                continue
            dx      = event.pos[0] - touch_start[0]
            dy      = event.pos[1] - touch_start[1]
            elapsed = time_mod.time() - touch_start_time
            is_tap  = abs(dx) < 12 and abs(dy) < 12

            if current_app:
                if dx > 60 and abs(dy) < 40:
                    current_app = None
                elif dy > 80 and abs(dx) < 40:
                    current_app = None
                elif is_tap:
                    try:
                        app_instances[current_app].handle_input(event)
                    except:
                        pass
            else:
                if dx < -50 and abs(dy) < 40 and current_page == 0:
                    current_page = 1
                elif dx > 50 and abs(dy) < 40 and current_page == 1:
                    current_page = 0
                elif is_tap:
                    name = get_tapped_app(event.pos)
                    if name:
                        current_app = name
            touch_start = None

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                current_app = None
            elif current_app:
                try:
                    app_instances[current_app].handle_input(event)
                except:
                    pass

    if current_app:
        draw_app_screen()
    else:
        draw_home()

    pygame.display.flip()
    clock.tick(FPS)
