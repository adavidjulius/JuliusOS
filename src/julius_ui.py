import pygame
import sys
import os
import datetime
import math
import time
import json
import socket
import threading

sys.path.insert(0, os.path.dirname(__file__))

from apps.terminal.terminal               import Terminal
from apps.wifi.wifi                       import WiFiScanner
from apps.ir.ir                           import IRRemote
from apps.bluetooth.bluetooth             import BluetoothScanner
from apps.gpio.gpio                       import GPIOControl
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
from system.control_center               import ControlCenter
from system.notification_center          import NotificationCenter
from system.spotlight                    import Spotlight
from system.julius_ai                    import JuliusAI
from system.julius_drop                  import JuliusDrop
from system.julius_cloud                 import JuliusCloud
from system.lock_animation               import LockAnimation

W, H  = 320, 480
FPS   = 60

BG      = (8,   8,  18)
CARD    = (28,  28,  32)
WHITE   = (255, 255, 255)
DIM     = (120, 120, 130)
DOCK_BG = (24,  24,  28)
GREEN   = (48,  209,  88)
BLUE    = (10,  132, 255)
RED     = (255,  69,  58)
PURPLE  = (191,  90, 242)
TEAL    = (90,  200, 250)
ORANGE  = (255, 159,  10)

SETTINGS_FILE = "julius_settings.json"

DEFAULT_SETTINGS = {
    "wifi"         : True,
    "bluetooth"    : True,
    "brightness"   : 100,
    "volume"       : 80,
    "airplane"     : False,
    "dark_mode"    : True,
    "notifications": True,
    "fingerprint"  : True,
    "ota_enabled"  : True,
    "hotspot"      : False,
    "admin_device" : "",
    "device_name"  : "Julius",
    "version"      : "Julius OS v1.1",
}

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE) as f:
            return json.load(f)
    return DEFAULT_SETTINGS.copy()

def save_settings(c):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(c, f)

cfg = load_settings()

APPS = [
    {"name":"Terminal",  "bg":(0,50,25),    "ac":(0,255,128),   "page":0},
    {"name":"WiFi",      "bg":(0,25,70),    "ac":(64,156,255),  "page":0},
    {"name":"IR",        "bg":(70,0,0),     "ac":(255,100,90),  "page":0},
    {"name":"Bluetooth", "bg":(25,0,75),    "ac":(191,90,242),  "page":0},
    {"name":"Connect",   "bg":(0,55,50),    "ac":(99,230,190),  "page":0},
    {"name":"Transfer",  "bg":(40,0,75),    "ac":(218,143,255), "page":0},
    {"name":"Scanner",   "bg":(0,45,30),    "ac":(48,209,88),   "page":0},
    {"name":"Files",     "bg":(25,45,0),    "ac":(168,255,120), "page":0},
    {"name":"SysMon",    "bg":(0,45,65),    "ac":(100,210,255), "page":0},
    {"name":"SSH",       "bg":(50,30,0),    "ac":(255,159,10),  "page":0},
    {"name":"Notes",     "bg":(50,42,0),    "ac":(255,224,102), "page":0},
    {"name":"NetTools",  "bg":(0,20,60),    "ac":(90,200,250),  "page":0},
    {"name":"Packets",   "bg":(65,0,48),    "ac":(255,45,120),  "page":0},
    {"name":"Clipboard", "bg":(20,30,0),    "ac":(200,255,120), "page":0},
    {"name":"Hotspot",   "bg":(65,0,15),    "ac":(255,107,107), "page":0},
    {"name":"GPIO",      "bg":(70,48,0),    "ac":(255,214,10),  "page":0},
    {"name":"Calc",      "bg":(0,22,22),    "ac":(0,229,255),   "page":1},
    {"name":"Todo",      "bg":(0,48,0),     "ac":(105,255,71),  "page":1},
    {"name":"Passwords", "bg":(48,0,15),    "ac":(255,92,138),  "page":1},
    {"name":"Weather",   "bg":(0,15,48),    "ac":(116,185,255), "page":1},
    {"name":"Hasher",    "bg":(22,0,48),    "ac":(224,64,251),  "page":1},
    {"name":"Encoder",   "bg":(0,48,0),     "ac":(0,230,118),   "page":1},
    {"name":"NetMon",    "bg":(0,15,48),    "ac":(64,196,255),  "page":1},
    {"name":"Editor",    "bg":(42,30,0),    "ac":(255,215,64),  "page":1},
    {"name":"Timer",     "bg":(48,15,0),    "ac":(255,109,0),   "page":1},
    {"name":"WakeOnLAN", "bg":(0,48,30),    "ac":(105,255,218), "page":1},
    {"name":"SpeedTest", "bg":(0,22,0),     "ac":(118,255,3),   "page":1},
    {"name":"ProcKill",  "bg":(48,0,0),     "ac":(255,23,68),   "page":1},
    {"name":"NetMapper", "bg":(0,15,48),    "ac":(68,138,255),  "page":1},
    {"name":"SysInfo",   "bg":(22,0,22),    "ac":(234,128,252), "page":1},
    {"name":"Firewall",  "bg":(48,8,0),     "ac":(255,110,64),  "page":1},
    {"name":"Logs",      "bg":(0,22,0),     "ac":(185,246,202), "page":1},
    {"name":"USB",       "bg":(22,15,0),    "ac":(255,229,127), "page":1},
    {"name":"Drop",      "bg":(0,30,50),    "ac":(90,200,250),  "page":1},
    {"name":"Cloud",     "bg":(20,0,50),    "ac":(191,90,242),  "page":1},
    {"name":"AI",        "bg":(26,0,51),    "ac":(191,90,242),  "page":1},
    {"name":"Settings",  "bg":(28,28,32),   "ac":(142,142,147), "page":1},
]

DOCK_NAMES = ["Terminal", "WiFi", "AI", "Settings"]

SETTINGS_SECTIONS = [
    {"title":"Device","items":[
        {"key":"device_name","label":"Device Name","type":"text"},
        {"key":"version",    "label":"Version",    "type":"info"},
    ]},
    {"title":"Wireless","items":[
        {"key":"wifi",      "label":"WiFi",         "type":"toggle"},
        {"key":"bluetooth", "label":"Bluetooth",    "type":"toggle"},
        {"key":"hotspot",   "label":"Hotspot",      "type":"toggle"},
        {"key":"airplane",  "label":"Airplane Mode","type":"toggle"},
    ]},
    {"title":"Security","items":[
        {"key":"fingerprint",  "label":"Fingerprint",   "type":"toggle"},
        {"key":"notifications","label":"Notifications", "type":"toggle"},
    ]},
    {"title":"Display","items":[
        {"key":"brightness","label":"Brightness","type":"slider"},
        {"key":"dark_mode", "label":"Dark Mode", "type":"toggle"},
    ]},
    {"title":"Sound","items":[
        {"key":"volume","label":"Volume","type":"slider"},
    ]},
    {"title":"Updates","items":[
        {"key":"ota_enabled", "label":"OTA Updates",  "type":"toggle"},
        {"key":"admin_device","label":"Admin Device", "type":"text"},
    ]},
]

pygame.init()
screen     = pygame.display.set_mode((W, H))
pygame.display.set_caption("Julius OS")
clock      = pygame.time.Clock()

font_clock  = pygame.font.SysFont("helvetica", 72, bold=False)
font_date   = pygame.font.SysFont("helvetica", 15)
font_status = pygame.font.SysFont("helvetica", 13, bold=True)
font_label  = pygame.font.SysFont("helvetica", 10)
font_title  = pygame.font.SysFont("helvetica", 20, bold=True)
font_body   = pygame.font.SysFont("helvetica", 13)
font_small  = pygame.font.SysFont("helvetica", 11)
font_hint   = pygame.font.SysFont("helvetica", 12)

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
}

control_center = ControlCenter(screen, font_title, font_small, cfg, save_settings)
notif_center   = NotificationCenter(screen, font_body, font_small)
spotlight_sys  = Spotlight(screen, font_body, font_small, APPS)
julius_ai      = JuliusAI(screen, font_body, font_small)
julius_drop    = JuliusDrop(screen, font_body, font_small)
julius_cloud   = JuliusCloud(screen, font_body, font_small)
lock_anim      = LockAnimation(screen, W, H)

STATE_LOCK     = "lock"
STATE_HOME     = "home"
STATE_APP      = "app"
STATE_SETTINGS = "settings"

state             = STATE_LOCK
swipe_count       = 0
current_app       = None
current_page      = 0
touch_start       = None
touch_time        = 0
settings_scroll   = 0
items_flat_cache  = []

show_cc           = False
show_notif        = False
show_spotlight    = False
show_ai           = False
show_drop         = False
show_cloud        = False

fp_scanning       = False
fp_start_time     = 0

def rr(surf, color, rect, radius):
    x, y, w, h = rect
    r = min(radius, w//2, h//2)
    pygame.draw.rect(surf, color, (x+r, y, w-2*r, h))
    pygame.draw.rect(surf, color, (x, y+r, w, h-2*r))
    for cx2, cy2 in [(x+r,y+r),(x+w-r,y+r),(x+r,y+h-r),(x+w-r,y+h-r)]:
        pygame.draw.circle(surf, color, (cx2,cy2), r)

def draw_icon(surf, app, x, y, size=60):
    ac   = app["ac"]
    bg   = app["bg"]
    name = app["name"]
    r2   = size // 6
    rr(surf, bg, (x,y,size,size), r2)
    cx2 = x + size//2
    cy2 = y + size//2

    if name == "Terminal":
        pts = [(x+8,cy2-4),(cx2-4,cy2),(x+8,cy2+4)]
        pygame.draw.lines(surf,ac,False,pts,2)
        pygame.draw.line(surf,ac,(cx2+2,cy2+4),(x+size-8,cy2+4),2)
    elif name == "WiFi":
        for rad,alpha in [(14,60),(10,130),(6,200)]:
            s2=pygame.Surface((size*2,size*2),pygame.SRCALPHA)
            pygame.draw.arc(s2,(*ac,alpha),(size-rad,size-rad//2,rad*2,rad),0,math.pi,2)
            surf.blit(s2,(x-size//2,y-size//2))
        pygame.draw.circle(surf,ac,(cx2,cy2+5),2)
    elif name == "IR":
        pygame.draw.circle(surf,ac,(cx2,cy2),5)
        for ang in range(0,360,90):
            r3=math.radians(ang)
            sx2=cx2+int(math.cos(r3)*7)
            sy2=cy2+int(math.sin(r3)*7)
            ex=cx2+int(math.cos(r3)*13)
            ey=cy2+int(math.sin(r3)*13)
            pygame.draw.line(surf,(*ac,120),(sx2,sy2),(ex,ey),2)
    elif name == "Bluetooth":
        mid=cx2
        t2=cy2-10
        b2=cy2+10
        pygame.draw.lines(surf,ac,False,
            [(mid-6,t2+4),(mid+6,cy2),(mid-6,b2-4),
             (mid-6,t2+4),(mid,t2),(mid+6,cy2),(mid,b2),(mid-6,b2-4)],2)
    elif name == "GPIO":
        pygame.draw.rect(surf,ac,(cx2-8,cy2-8,16,16),2)
        for dy2 in [-4,4]:
            pygame.draw.circle(surf,ac,(cx2-13,cy2+dy2),2)
            pygame.draw.circle(surf,ac,(cx2+13,cy2+dy2),2)
            pygame.draw.line(surf,ac,(cx2-8,cy2+dy2),(cx2-13,cy2+dy2),1)
            pygame.draw.line(surf,ac,(cx2+8,cy2+dy2),(cx2+13,cy2+dy2),1)
    elif name == "Connect":
        pygame.draw.circle(surf,ac,(cx2-10,cy2),4,2)
        pygame.draw.circle(surf,ac,(cx2+8,cy2-7),3,2)
        pygame.draw.circle(surf,ac,(cx2+8,cy2+7),3,2)
        pygame.draw.line(surf,(*ac,150),(cx2-6,cy2),(cx2+5,cy2-5),1)
        pygame.draw.line(surf,(*ac,150),(cx2-6,cy2),(cx2+5,cy2+5),1)
    elif name == "Transfer":
        pygame.draw.line(surf,ac,(x+8,cy2-4),(x+size-8,cy2-4),2)
        pygame.draw.lines(surf,ac,False,
            [(x+size-13,cy2-8),(x+size-8,cy2-4),(x+size-13,cy2)],2)
        pygame.draw.line(surf,(*ac,150),(x+8,cy2+4),(x+size-8,cy2+4),2)
        pygame.draw.lines(surf,(*ac,150),False,
            [(x+12,cy2),(x+8,cy2+4),(x+12,cy2+8)],2)
    elif name == "Scanner":
        pygame.draw.circle(surf,ac,(cx2-3,cy2-3),8,2)
        pygame.draw.line(surf,ac,(cx2+3,cy2+3),(cx2+10,cy2+10),2)
        pygame.draw.line(surf,(*ac,150),(cx2-7,cy2-3),(cx2+1,cy2-3),1)
        pygame.draw.line(surf,(*ac,150),(cx2-3,cy2-7),(cx2-3,cy2+1),1)
    elif name == "Files":
        pygame.draw.polygon(surf,ac,
            [(x+8,y+8),(x+size-8,y+8),(x+size-8,y+size-8),(x+8,y+size-8)],2)
        for i2,ly2 in enumerate([cy2-4,cy2+1,cy2+6]):
            pygame.draw.line(surf,(*ac,200-i2*60),(x+13,ly2),(x+size-13,ly2),2)
    elif name == "SysMon":
        pts3=[(x+4,cy2+4),(x+9,cy2-4),(x+14,cy2+2),(cx2,cy2-8),
              (cx2+7,cy2),(cx2+13,cy2-4),(x+size-4,cy2+2)]
        pygame.draw.lines(surf,ac,False,pts3,2)
    elif name == "SSH":
        pygame.draw.rect(surf,ac,(x+6,y+10,size-12,size-20),2,border_radius=3)
        t3=font_small.render("SSH",True,ac)
        surf.blit(t3,(cx2-t3.get_width()//2,cy2-t3.get_height()//2))
    elif name == "Notes":
        pts4=[(x+8,y+8),(x+size-8,y+8),(x+size-8,y+size-10),
              (x+size-14,y+size-8),(x+8,y+size-8)]
        pygame.draw.polygon(surf,ac,pts4,2)
        for i2,ly2 in enumerate([cy2-6,cy2-1,cy2+4,cy2+9]):
            pygame.draw.line(surf,(*ac,220-i2*55),(x+12,ly2),(x+size-12,ly2),1)
    elif name == "Passwords":
        pygame.draw.rect(surf,ac,(cx2-9,cy2-2,18,12),2,border_radius=3)
        pygame.draw.arc(surf,ac,(cx2-7,cy2-12,14,14),0,math.pi,2)
        pygame.draw.circle(surf,ac,(cx2,cy2+3),3)
    elif name == "Calc":
        pygame.draw.rect(surf,ac,(x+8,y+8,size-16,size-16),2,border_radius=4)
        pygame.draw.rect(surf,(*ac,60),(x+10,y+10,size-20,10))
        for r3 in range(3):
            for c3 in range(3):
                pygame.draw.circle(surf,ac,(x+14+c3*8,cy2+2+r3*7),2)
    elif name == "Todo":
        for i2,(ly2,op) in enumerate([(cy2-7,255),(cy2,180),(cy2+7,100)]):
            pygame.draw.lines(surf,(*ac,op),False,
                [(x+10,ly2),(x+15,ly2+5),(x+21,ly2-2)],2)
            pygame.draw.line(surf,(*ac,op//2),(x+24,ly2),(x+size-10,ly2),2)
    elif name == "Weather":
        pygame.draw.circle(surf,ac,(cx2-4,cy2-3),7,2)
        pygame.draw.arc(surf,ac,(cx2-2,cy2-9,16,14),math.pi*0.8,math.pi*2,2)
        for i2,rx2 in enumerate([cx2-8,cx2-2,cx2+4]):
            pygame.draw.line(surf,(*ac,160-i2*40),(rx2,cy2+7),(rx2-2,cy2+13),2)
    elif name == "Hasher":
        pygame.draw.line(surf,ac,(cx2-6,cy2-10),(cx2-8,cy2+10),2)
        pygame.draw.line(surf,ac,(cx2+2,cy2-10),(cx2,cy2+10),2)
        pygame.draw.line(surf,(*ac,180),(cx2-10,cy2-3),(cx2+6,cy2-3),2)
        pygame.draw.line(surf,(*ac,180),(cx2-11,cy2+4),(cx2+5,cy2+4),2)
    elif name == "Encoder":
        pygame.draw.rect(surf,ac,(x+6,y+12,12,14),2,border_radius=2)
        pygame.draw.rect(surf,ac,(x+size-18,y+12,12,14),2,border_radius=2)
        pygame.draw.line(surf,ac,(x+18,cy2-2),(x+size-18,cy2-2),2)
        pygame.draw.line(surf,(*ac,150),(x+18,cy2+3),(x+size-18,cy2+3),1)
    elif name == "NetMon":
        pygame.draw.rect(surf,ac,(x+4,y+8,size-8,size-20),2,border_radius=3)
        pts5=[(x+8,cy2-2),(x+13,cy2-7),(x+18,cy2-1),
              (cx2,cy2-10),(cx2+7,cy2-3),(cx2+13,cy2-6),(x+size-8,cy2-2)]
        pygame.draw.lines(surf,ac,False,pts5,2)
    elif name == "Editor":
        pts6=[(cx2+8,cy2-10),(cx2-8,cy2+8),(cx2-10,cy2+10),(cx2-8,cy2+8)]
        pygame.draw.lines(surf,ac,False,pts6,2)
        pygame.draw.line(surf,(*ac,100),(cx2-10,cy2+12),(cx2+4,cy2+12),1)
    elif name == "Timer":
        pygame.draw.circle(surf,ac,(cx2,cy2+2),10,2)
        pygame.draw.line(surf,ac,(cx2,cy2+2),(cx2,cy2-4),2)
        pygame.draw.line(surf,ac,(cx2,cy2+2),(cx2+5,cy2+5),2)
        pygame.draw.line(surf,(*ac,150),(cx2-5,y+8),(cx2+5,y+8),2)
    elif name == "WakeOnLAN":
        pygame.draw.rect(surf,ac,(x+6,y+12,size-12,size-24),2,border_radius=3)
        for i2 in range(4):
            pygame.draw.line(surf,ac,(x+11+i2*7,cy2-3),(x+13+i2*7,cy2+3),2)
    elif name == "SpeedTest":
        pygame.draw.arc(surf,ac,(x+6,y+10,size-12,size-12),math.pi,0,3)
        pygame.draw.line(surf,ac,(cx2,cy2),(cx2+8,cy2-8),2)
        pygame.draw.circle(surf,ac,(cx2,cy2),3)
    elif name == "ProcKill":
        pygame.draw.rect(surf,ac,(x+6,y+10,size-12,size-20),2,border_radius=3)
        pygame.draw.line(surf,ac,(cx2-7,cy2-5),(cx2+7,cy2+5),2)
        pygame.draw.line(surf,ac,(cx2+7,cy2-5),(cx2-7,cy2+5),2)
    elif name == "NetMapper":
        for rad2,op in [(12,50),(8,120),(4,200)]:
            pygame.draw.circle(surf,(*ac,op),(cx2,cy2),rad2,1)
        pygame.draw.circle(surf,ac,(cx2,cy2),2)
        pygame.draw.line(surf,(*ac,60),(x+4,cy2),(x+size-4,cy2),1)
        pygame.draw.line(surf,(*ac,60),(cx2,y+4),(cx2,y+size-4),1)
    elif name == "SysInfo":
        pygame.draw.circle(surf,ac,(cx2,cy2),11,2)
        pygame.draw.line(surf,ac,(cx2,cy2-2),(cx2,cy2+7),3)
        pygame.draw.circle(surf,ac,(cx2,cy2-6),2)
    elif name == "Firewall":
        pts7=[(cx2,y+6),(x+size-8,cy2-6),(x+size-8,cy2+4),
              (cx2,y+size-6),(x+8,cy2+4),(x+8,cy2-6),(cx2,y+6)]
        pygame.draw.polygon(surf,ac,pts7,2)
        pygame.draw.line(surf,ac,(cx2,cy2-5),(cx2,cy2+5),2)
    elif name == "Logs":
        pygame.draw.rect(surf,ac,(x+8,y+8,size-16,size-16),2,border_radius=3)
        for i2,ly2 in enumerate([cy2-6,cy2-1,cy2+4,cy2+9]):
            pygame.draw.line(surf,(*ac,210-i2*50),(x+12,ly2),(x+size-12,ly2),2)
    elif name == "USB":
        pygame.draw.line(surf,ac,(cx2,y+8),(cx2,y+size-10),2)
        pygame.draw.lines(surf,ac,False,
            [(cx2-6,y+13),(cx2,y+8),(cx2+6,y+13)],2)
        pygame.draw.rect(surf,ac,(cx2-5,cy2-6,10,6),2)
        pygame.draw.rect(surf,ac,(cx2-5,cy2+2,10,6),2)
        pygame.draw.circle(surf,ac,(cx2,y+size-10),4,2)
    elif name == "Clipboard":
        pygame.draw.rect(surf,ac,(x+8,y+10,size-16,size-18),2,border_radius=3)
        pygame.draw.rect(surf,ac,(cx2-6,y+7,12,6),2,border_radius=2)
        for i2,ly2 in enumerate([cy2-4,cy2+1,cy2+6]):
            pygame.draw.line(surf,(*ac,200-i2*60),(x+13,ly2),(x+size-13,ly2),1)
    elif name == "Hotspot":
        pygame.draw.arc(surf,ac,(x+4,y+8,size-8,size-8),
            math.pi*0.1,math.pi*0.9,2)
        pygame.draw.circle(surf,ac,(cx2,cy2+4),3)
        pygame.draw.line(surf,(*ac,150),(cx2,cy2+7),(cx2,cy2+13),2)
    elif name == "NetTools":
        pygame.draw.rect(surf,ac,(cx2-8,y+8,10,8),2)
        pygame.draw.rect(surf,ac,(x+8,cy2,10,8),2)
        pygame.draw.rect(surf,ac,(x+size-18,cy2,10,8),2)
        pygame.draw.line(surf,ac,(cx2-3,y+16),(cx2-3,cy2),1)
        pygame.draw.line(surf,ac,(cx2-3,cy2+4),(x+18,cy2+4),1)
        pygame.draw.line(surf,ac,(cx2-3,cy2+4),(x+size-13,cy2+4),1)
    elif name == "Packets":
        pygame.draw.rect(surf,ac,(x+4,y+12,10,8),2)
        pygame.draw.rect(surf,ac,(x+size-14,y+12,10,8),2)
        pygame.draw.line(surf,ac,(x+14,cy2),(x+size-14,cy2),2)
        pygame.draw.lines(surf,ac,False,
            [(x+size-16,cy2-3),(x+size-14,cy2),(x+size-16,cy2+3)],2)
    elif name == "Drop":
        for rad2 in [12,8,4]:
            pygame.draw.circle(surf,(*ac,100+rad2*10),(cx2,cy2),rad2,1)
        pygame.draw.line(surf,ac,(cx2,cy2-6),(cx2,cy2+4),2)
        pygame.draw.lines(surf,ac,False,
            [(cx2-4,cy2+1),(cx2,cy2+5),(cx2+4,cy2+1)],2)
    elif name == "Cloud":
        pygame.draw.arc(surf,ac,(cx2-14,cy2-8,16,16),0,math.pi,2)
        pygame.draw.arc(surf,ac,(cx2-4,cy2-12,16,16),0,math.pi,2)
        pygame.draw.rect(surf,ac,(cx2-14,cy2,28,8),2)
        pygame.draw.line(surf,ac,(cx2,cy2+8),(cx2,cy2+14),2)
        pygame.draw.lines(surf,ac,False,
            [(cx2-4,cy2+11),(cx2,cy2+15),(cx2+4,cy2+11)],2)
    elif name == "AI":
        pygame.draw.circle(surf,ac,(cx2,cy2),10,2)
        t3=font_small.render("AI",True,ac)
        surf.blit(t3,(cx2-t3.get_width()//2,cy2-t3.get_height()//2))
        for ang in [0,120,240]:
            r3=math.radians(ang)
            pygame.draw.line(surf,(*ac,120),
                (cx2+int(math.cos(r3)*10),cy2+int(math.sin(r3)*10)),
                (cx2+int(math.cos(r3)*16),cy2+int(math.sin(r3)*16)),2)
    elif name == "Settings":
        pygame.draw.circle(surf,ac,(cx2,cy2),5,2)
        for ang in range(0,360,45):
            r3=math.radians(ang)
            x1=cx2+int(math.cos(r3)*8)
            y1=cy2+int(math.sin(r3)*8)
            x2=cx2+int(math.cos(r3)*12)
            y2=cy2+int(math.sin(r3)*12)
            pygame.draw.line(surf,ac,(x1,y1),(x2,y2),2)
    else:
        t3=font_small.render(name[:3],True,ac)
        surf.blit(t3,(cx2-t3.get_width()//2,cy2-t3.get_height()//2))

def draw_status_bar():
    now = datetime.datetime.now()
    t   = now.strftime("%H:%M")
    ts  = font_status.render(t, True, WHITE)
    screen.blit(ts, (16, 12))
    bat_x = W-52
    pygame.draw.rect(screen,WHITE,(bat_x,12,28,13),1,border_radius=3)
    pygame.draw.rect(screen,WHITE,(bat_x+28,15,3,7),border_radius=1)
    pygame.draw.rect(screen,GREEN,(bat_x+2,14,22,9),border_radius=2)
    for i in range(3):
        bx=W-92+i*7
        bh=5+i*2
        pygame.draw.rect(screen,(*WHITE,80+i*60),(bx,18-bh//2,5,bh),border_radius=1)
    unread = notif_center.unread_count()
    if unread > 0:
        nb = font_small.render(str(unread),True,WHITE)
        rr(screen,RED,(W//2-8,10,16,16),8)
        screen.blit(nb,(W//2-nb.get_width()//2,12))

def draw_home_bar():
    bx=W//2-50
    pygame.draw.rect(screen,(*WHITE,90),(bx,H-8,100,4),border_radius=2)

def draw_lock_screen():
    screen.fill(BG)
    now      = datetime.datetime.now()
    time_str = now.strftime("%H:%M")
    date_str = now.strftime("%A, %d %B")
    ts = font_clock.render(time_str,True,WHITE)
    ds = font_date.render(date_str, True,(*WHITE,180))
    screen.blit(ts,(W//2-ts.get_width()//2,H//2-140))
    screen.blit(ds,(W//2-ds.get_width()//2,H//2-60))

    lock_anim.draw()

    if swipe_count == 0:
        hint=font_hint.render("swipe left twice to unlock",True,(*WHITE,100))
    elif swipe_count == 1:
        hint=font_hint.render("swipe left once more",True,(*WHITE,160))
    else:
        hint=font_hint.render("",True,WHITE)
    screen.blit(hint,(W//2-hint.get_width()//2,H-50))

    for i in range(3):
        col2=WHITE if i<swipe_count else (*WHITE,40)
        pygame.draw.circle(screen,col2,(W//2-8+i*8,H-30),3)

    draw_home_bar()

def draw_home_screen():
    screen.fill(BG)
    draw_status_bar()
    now      = datetime.datetime.now()
    time_str = now.strftime("%H:%M")
    date_str = now.strftime("%A, %B %d")
    ts=font_clock.render(time_str,True,WHITE)
    ds=font_date.render(date_str, True,(*WHITE,160))
    screen.blit(ts,(W//2-ts.get_width()//2,36))
    screen.blit(ds,(W//2-ds.get_width()//2,108))

    page_apps=[a for a in APPS if a["page"]==current_page]
    cols=4
    pad=9
    icon_size=(W-pad*(cols+1))//cols
    start_y=132

    for i,app in enumerate(page_apps):
        col2=i%cols
        row2=i//cols
        ix=pad+col2*(icon_size+pad)
        iy=start_y+row2*(icon_size+20+5)
        draw_icon(screen,app,ix,iy,icon_size)
        lbl=font_label.render(app["name"],True,(*WHITE,200))
        screen.blit(lbl,(ix+icon_size//2-lbl.get_width()//2,iy+icon_size+2))

    dot_y=H-78
    for i in range(2):
        col3=WHITE if i==current_page else (*WHITE,70)
        pygame.draw.circle(screen,col3,(W//2-6+i*12,dot_y),
            4 if i==current_page else 3)

    dock_y=H-70
    rr(screen,DOCK_BG,(12,dock_y,W-24,60),18)
    dock_apps=[a for a in APPS if a["name"] in DOCK_NAMES]
    dsz=46
    dpd=(W-24-len(dock_apps)*dsz)//(len(dock_apps)+1)
    for i,app in enumerate(dock_apps):
        dx=12+dpd*(i+1)+dsz*i
        draw_icon(screen,app,dx,dock_y+7,dsz)

    draw_home_bar()

def draw_app_screen():
    app=next((a for a in APPS if a["name"]==current_app),None)
    if not app:
        return
    screen.fill(BG)
    draw_status_bar()
    pygame.draw.line(screen,(40,40,55),(0,36),(W,36),1)
    title=font_title.render(current_app,True,WHITE)
    screen.blit(title,(W//2-title.get_width()//2,42))
    try:
        app_instances[current_app].draw()
    except Exception as e:
        err=font_body.render(f"Error: {str(e)[:28]}",True,RED)
        screen.blit(err,(10,H//2))
    draw_home_bar()

def draw_settings():
    screen.fill(BG)
    draw_status_bar()
    pygame.draw.line(screen,(40,40,55),(0,36),(W,36),1)
    title=font_title.render("Settings",True,WHITE)
    screen.blit(title,(W//2-title.get_width()//2,42))

    y=70-settings_scroll
    items_flat=[]
    for section in SETTINGS_SECTIONS:
        sh=font_hint.render(section["title"].upper(),True,(*WHITE,100))
        if 36<y<H-60:
            screen.blit(sh,(16,y))
        y+=22
        for item in section["items"]:
            if 36<y<H-60:
                rr(screen,CARD,(12,y,W-24,36),8)
                lbl=font_body.render(item["label"],True,WHITE)
                screen.blit(lbl,(20,y+10))
                val=cfg.get(item["key"],"")
                if item["type"]=="toggle":
                    col4=GREEN if val else (80,80,90)
                    rr(screen,col4,(W-58,y+8,40,20),10)
                    cx3=W-38+10 if val else W-58+10
                    pygame.draw.circle(screen,WHITE,(cx3,y+18),8)
                elif item["type"]=="slider":
                    bw=80
                    bx=W-100
                    pygame.draw.rect(screen,(60,60,70),(bx,y+14,bw,8),border_radius=4)
                    fw=int(bw*val/100)
                    pygame.draw.rect(screen,BLUE,(bx,y+14,fw,8),border_radius=4)
                    pygame.draw.circle(screen,WHITE,(bx+fw,y+18),6)
                elif item["type"] in ["text","info"]:
                    vt=font_small.render(str(val)[:18],True,(*WHITE,140))
                    screen.blit(vt,(W-vt.get_width()-16,y+12))
            items_flat.append({"y":y,"item":item})
            y+=44
        y+=8

    draw_home_bar()
    return items_flat

def handle_settings_tap(pos,items):
    for entry in items:
        iy=entry["y"]
        itm=entry["item"]
        if iy<pos[1]<iy+40:
            key=itm["key"]
            if itm["type"]=="toggle":
                cfg[key]=not cfg.get(key,False)
                save_settings(cfg)
            elif itm["type"]=="slider":
                bx=W-100
                bw=80
                rel=max(0,min(pos[0]-bx,bw))
                cfg[key]=int(rel/bw*100)
                save_settings(cfg)

def get_tapped_app(pos):
    page_apps=[a for a in APPS if a["page"]==current_page]
    cols=4
    pad=9
    icon_size=(W-pad*(cols+1))//cols
    start_y=132
    for i,app in enumerate(page_apps):
        col2=i%cols
        row2=i//cols
        ix=pad+col2*(icon_size+pad)
        iy=start_y+row2*(icon_size+20+5)
        if ix<=pos[0]<=ix+icon_size and iy<=pos[1]<=iy+icon_size:
            return app["name"]
    dock_apps=[a for a in APPS if a["name"] in DOCK_NAMES]
    dsz=46
    dock_y=H-70
    dpd=(W-24-len(dock_apps)*dsz)//(len(dock_apps)+1)
    for i,app in enumerate(dock_apps):
        dx=12+dpd*(i+1)+dsz*i
        if dx<=pos[0]<=dx+dsz and dock_y+7<=pos[1]<=dock_y+53:
            return app["name"]
    return None

while True:
    for event in pygame.event.get():
        if event.type==pygame.QUIT:
            pygame.quit()
            sys.exit()

        if event.type==pygame.MOUSEBUTTONDOWN:
            touch_start=event.pos
            touch_time=time.time()

        if event.type==pygame.MOUSEBUTTONUP:
            if touch_start is None:
                continue
            dx=event.pos[0]-touch_start[0]
            dy=event.pos[1]-touch_start[1]
            is_tap          = abs(dx)<14 and abs(dy)<14
            is_swipe_left   = dx<-50 and abs(dy)<60
            is_swipe_right  = dx>50  and abs(dy)<60
            is_swipe_down   = dy>70  and abs(dx)<60
            is_swipe_up     = dy<-50 and abs(dx)<60
            from_top        = touch_start[1]<80
            from_bottom     = touch_start[1]>H-100

            # Handle overlays first
            if show_cc:
                if control_center.handle_touch(event.pos):
                    if is_swipe_down:
                        show_cc=False
                        control_center.hide()
                    touch_start=None
                    continue

            if show_notif:
                if notif_center.handle_touch(event.pos):
                    if is_swipe_up:
                        show_notif=False
                        notif_center.hide()
                    touch_start=None
                    continue

            if show_spotlight:
                res=spotlight_sys.handle_touch(event.pos)
                if res=="hide":
                    show_spotlight=False
                elif res and isinstance(res,dict):
                    if res.get("type")=="app":
                        current_app=res["name"]
                        state=STATE_APP
                        show_spotlight=False
                touch_start=None
                continue

            if show_ai:
                julius_ai.handle_touch(event.pos)
                if is_swipe_right or is_swipe_down:
                    show_ai=False
                    julius_ai.hide()
                touch_start=None
                continue

            if show_drop:
                julius_drop.handle_touch(event.pos)
                if is_swipe_right or is_swipe_down:
                    show_drop=False
                    julius_drop.hide()
                touch_start=None
                continue

            if show_cloud:
                julius_cloud.handle_touch(event.pos)
                if is_swipe_right or is_swipe_down:
                    show_cloud=False
                    julius_cloud.hide()
                touch_start=None
                continue

            # State machine
            if state==STATE_LOCK:
                if is_swipe_left:
                    swipe_count+=1
                    if swipe_count>=2:
                        lock_anim.start_scan()
                        result=True
                        lock_anim.set_result(result)
                        if result:
                            state=STATE_HOME
                            swipe_count=0

            elif state==STATE_HOME:
                if is_swipe_down and from_top:
                    notif_center.show()
                    show_notif=True
                elif is_swipe_up and from_bottom:
                    control_center.show()
                    show_cc=True
                elif is_swipe_up and not from_bottom:
                    spotlight_sys.show()
                    show_spotlight=True
                elif is_swipe_down and not from_top:
                    state=STATE_LOCK
                    swipe_count=0
                elif is_swipe_left and current_page==0:
                    current_page=1
                elif is_swipe_right and current_page==1:
                    current_page=0
                elif is_tap:
                    name=get_tapped_app(event.pos)
                    if name=="Settings":
                        state=STATE_SETTINGS
                    elif name=="AI":
                        julius_ai.show()
                        show_ai=True
                    elif name=="Drop":
                        julius_drop.show()
                        show_drop=True
                    elif name=="Cloud":
                        julius_cloud.show()
                        show_cloud=True
                    elif name:
                        current_app=name
                        state=STATE_APP

            elif state==STATE_APP:
                if is_swipe_right or (is_swipe_down and from_top):
                    state=STATE_HOME
                    current_app=None
                elif is_tap:
                    try:
                        app_instances[current_app].handle_input(event)
                    except:
                        pass

            elif state==STATE_SETTINGS:
                if is_swipe_right or is_swipe_down:
                    state=STATE_HOME
                elif is_swipe_up:
                    settings_scroll=min(settings_scroll+40,500)
                elif is_tap:
                    handle_settings_tap(event.pos,items_flat_cache)

            touch_start=None

        if event.type==pygame.KEYDOWN:
            if show_spotlight:
                res=spotlight_sys.handle_key(event)
                if res=="hide":
                    show_spotlight=False
                elif res and isinstance(res,dict):
                    if res.get("type")=="app":
                        current_app=res["name"]
                        state=STATE_APP
                        show_spotlight=False
            elif show_ai:
                julius_ai.handle_key(event)
                if event.key==pygame.K_ESCAPE:
                    show_ai=False
            elif event.key==pygame.K_ESCAPE:
                if show_cc:
                    show_cc=False
                    control_center.hide()
                elif show_notif:
                    show_notif=False
                    notif_center.hide()
                elif state==STATE_APP:
                    state=STATE_HOME
                    current_app=None
                elif state==STATE_SETTINGS:
                    state=STATE_HOME
                elif state==STATE_HOME:
                    state=STATE_LOCK
                    swipe_count=0
            elif state==STATE_APP and current_app:
                try:
                    app_instances[current_app].handle_input(event)
                except:
                    pass

        if event.type==pygame.MOUSEWHEEL:
            if state==STATE_SETTINGS:
                settings_scroll=max(0,min(settings_scroll-event.y*20,500))

    # Draw
    if state==STATE_LOCK:
        draw_lock_screen()
    elif state==STATE_HOME:
        draw_home_screen()
    elif state==STATE_APP:
        draw_app_screen()
    elif state==STATE_SETTINGS:
        items_flat_cache=draw_settings()

    # Overlays on top
    if show_notif:
        notif_center.draw()
    if show_cc:
        control_center.draw()
    if show_spotlight:
        spotlight_sys.draw()
    if show_ai:
        julius_ai.draw()
    if show_drop:
        julius_drop.draw()
    if show_cloud:
        julius_cloud.draw()

    pygame.display.flip()
    clock.tick(FPS)
