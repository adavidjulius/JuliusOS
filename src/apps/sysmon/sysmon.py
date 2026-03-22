import pygame
import subprocess
import threading
import time

BG     = (10, 10, 20)
TEXT   = (255, 255, 255)
ACCENT = (0, 200, 255)
GREEN  = (0, 255, 100)
RED    = (255, 80,  80)
YELLOW = (255, 200,  0)
DIM    = (80, 80,   80)

class SysMon:
    def __init__(self, screen, font):
        self.screen  = screen
        self.font    = font
        self.cpu     = 0
        self.mem     = {}
        self.disk    = {}
        self.procs   = []
        self.running = True
        self.update()
        self.start_loop()

    def get_cpu(self):
        try:
            result = subprocess.check_output(
                ["top", "-bn1"], stderr=subprocess.DEVNULL
            ).decode()
            for line in result.split("\n"):
                if "Cpu" in line or "cpu" in line:
                    idle = float(line.split("id,")[0].strip().split()[-1])
                    return round(100 - idle, 1)
        except:
            return 0
        return 0

    def get_mem(self):
        try:
            with open("/proc/meminfo") as f:
                lines = f.readlines()
            info = {}
            for line in lines:
                parts = line.split()
                info[parts[0].rstrip(":")] = int(parts[1])
            total = info.get("MemTotal", 1)
            free  = info.get("MemAvailable", 0)
            used  = total - free
            return {
                "total"  : round(total / 1024),
                "used"   : round(used  / 1024),
                "percent": round(used  / total * 100, 1)
            }
        except:
            return {"total": 0, "used": 0, "percent": 0}

    def get_disk(self):
        try:
            result = subprocess.check_output(
                ["df", "-h", "/"], stderr=subprocess.DEVNULL
            ).decode().split("\n")[1].split()
            return {
                "total"  : result[1],
                "used"   : result[2],
                "percent": result[4]
            }
        except:
            return {"total": "?", "used": "?", "percent": "?"}

    def get_procs(self):
        try:
            result = subprocess.check_output(
                ["ps", "-eo", "pid,comm,%cpu", "--sort=-%cpu"],
                stderr=subprocess.DEVNULL
            ).decode().strip().split("\n")[1:6]
            procs = []
            for line in result:
                parts = line.strip().split()
                if len(parts) >= 3:
                    procs.append({
                        "pid" : parts[0],
                        "name": parts[1][:14],
                        "cpu" : parts[2]
                    })
            return procs
        except:
            return []

    def update(self):
        self.cpu   = self.get_cpu()
        self.mem   = self.get_mem()
        self.disk  = self.get_disk()
        self.procs = self.get_procs()

    def start_loop(self):
        def loop():
            while self.running:
                self.update()
                time.sleep(2)
        t = threading.Thread(target=loop)
        t.daemon = True
        t.start()

    def draw_bar(self, x, y, w, h, percent, color):
        pygame.draw.rect(self.screen, DIM,   (x, y, w, h), border_radius=3)
        fill = int(w * percent / 100)
        pygame.draw.rect(self.screen, color, (x, y, fill, h), border_radius=3)

    def draw(self):
        self.screen.fill(BG)
        title = self.font.render("System Monitor", True, ACCENT)
        self.screen.blit(title, (8, 8))
        pygame.draw.line(self.screen, ACCENT, (0, 24), (240, 24), 1)

        # CPU
        cpu_color = GREEN if self.cpu < 70 else YELLOW if self.cpu < 90 else RED
        cpu_label = self.font.render(f"CPU  {self.cpu}%", True, cpu_color)
        self.screen.blit(cpu_label, (8, 30))
        self.draw_bar(8, 42, 224, 8, self.cpu, cpu_color)

        # Memory
        mem_color = GREEN if self.mem.get("percent", 0) < 70 else YELLOW if self.mem.get("percent", 0) < 90 else RED
        mem_label = self.font.render(
            f"MEM  {self.mem.get('used',0)}MB / {self.mem.get('total',0)}MB", True, mem_color
        )
        self.screen.blit(mem_label, (8, 56))
        self.draw_bar(8, 68, 224, 8, self.mem.get("percent", 0), mem_color)

        # Disk
        disk_label = self.font.render(
            f"DISK {self.disk.get('used','?')} / {self.disk.get('total','?')}  {self.disk.get('percent','?')}", True, TEXT
        )
        self.screen.blit(disk_label, (8, 82))

        pygame.draw.line(self.screen, DIM, (0, 96), (240, 96), 1)

        # Processes
        header = self.font.render("PID   NAME           CPU", True, ACCENT)
        self.screen.blit(header, (8, 100))
        pygame.draw.line(self.screen, DIM, (0, 112), (240, 112), 1)

        y = 116
        for proc in self.procs:
            pid  = self.font.render(proc["pid"][:5],  True, DIM)
            name = self.font.render(proc["name"],      True, TEXT)
            cpu  = self.font.render(proc["cpu"] + "%", True, GREEN)
            self.screen.blit(pid,  (8,   y))
            self.screen.blit(name, (45,  y))
            self.screen.blit(cpu,  (200, y))
            y += 15

        hint = self.font.render("Auto refresh every 2s", True, DIM)
        self.screen.blit(hint, (8, 228))
        pygame.display.flip()

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                self.update()
