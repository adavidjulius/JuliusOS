import pygame
import subprocess
import platform
import socket
import os

BG     = (10, 10, 20)
TEXT   = (255, 255, 255)
ACCENT = (0, 200, 255)
GREEN  = (0, 255, 100)
DIM    = (80, 80,   80)
YELLOW = (255, 200,  0)

class SysInfo:
    def __init__(self, screen, font):
        self.screen = screen
        self.font   = font
        self.info   = {}
        self.scroll = 0
        self.lines  = []
        self.gather()

    def gather(self):
        info = []
        try:
            info.append(("OS",       platform.system()))
            info.append(("Release",  platform.release()))
            info.append(("Machine",  platform.machine()))
            info.append(("Python",   platform.python_version()))
            info.append(("Hostname", socket.gethostname()))
            try:
                ip = socket.gethostbyname(socket.gethostname())
                info.append(("IP", ip))
            except:
                info.append(("IP", "N/A"))
            try:
                with open("/proc/cpuinfo") as f:
                    for line in f:
                        if "model name" in line:
                            info.append(("CPU", line.split(":")[1].strip()[:20]))
                            break
            except:
                info.append(("CPU", platform.processor()[:20]))
            try:
                with open("/proc/meminfo") as f:
                    lines = f.readlines()
                total = int(lines[0].split()[1]) // 1024
                free  = int(lines[1].split()[1]) // 1024
                info.append(("RAM Total", f"{total} MB"))
                info.append(("RAM Free",  f"{free} MB"))
            except:
                pass
            try:
                result = subprocess.check_output(
                    ["df", "-h", "/"], stderr=subprocess.DEVNULL
                ).decode().split("\n")[1].split()
                info.append(("Disk Total", result[1]))
                info.append(("Disk Used",  result[2]))
                info.append(("Disk Free",  result[3]))
            except:
                pass
            try:
                with open("/proc/uptime") as f:
                    secs   = float(f.read().split()[0])
                    hours  = int(secs // 3600)
                    mins   = int((secs % 3600) // 60)
                    info.append(("Uptime", f"{hours}h {mins}m"))
            except:
                pass
            try:
                with open("/sys/class/thermal/thermal_zone0/temp") as f:
                    temp = int(f.read()) / 1000
                    info.append(("CPU Temp", f"{temp:.1f}C"))
            except:
                pass
        except Exception as e:
            info.append(("Error", str(e)))

        self.lines = info

    def draw(self):
        self.screen.fill(BG)
        title = self.font.render("System Info", True, ACCENT)
        self.screen.blit(title, (8, 8))
        pygame.draw.line(self.screen, ACCENT, (0, 24), (240, 24), 1)

        y = 28
        for i, (key, val) in enumerate(self.lines[self.scroll:self.scroll + 13]):
            k = self.font.render(f"{key:<12}", True, DIM)
            v = self.font.render(str(val)[:16], True, GREEN)
            self.screen.blit(k, (8,   y))
            self.screen.blit(v, (100, y))
            y += 15

        total = len(self.lines)
        count = self.font.render(f"{self.scroll + 1}-{min(self.scroll + 13, total)}/{total}", True, DIM)
        self.screen.blit(count, (8, 210))

        hint = self.font.render("UP DOWN=scroll  R=refresh", True, DIM)
        self.screen.blit(hint, (8, 228))
        pygame.display.flip()

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_DOWN:
                if self.scroll < len(self.lines) - 13:
                    self.scroll += 1
            elif event.key == pygame.K_UP:
                if self.scroll > 0:
                    self.scroll -= 1
            elif event.key == pygame.K_r:
                self.gather()
                self.scroll = 0
