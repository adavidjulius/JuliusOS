import pygame
import subprocess
import threading
import time

BG     = (10, 10, 20)
TEXT   = (255, 255, 255)
ACCENT = (0, 200, 255)
GREEN  = (0, 255, 100)
DIM    = (80, 80,   80)
RED    = (255, 80,  80)
YELLOW = (255, 200,  0)

class ProcessKiller:
    def __init__(self, screen, font):
        self.screen   = screen
        self.font     = font
        self.procs    = []
        self.selected = 0
        self.scroll   = 0
        self.status   = "Press R to refresh"
        self.filter   = ""
        self.mode     = "list"

    def refresh(self):
        try:
            result = subprocess.check_output(
                ["ps", "-eo", "pid,comm,%cpu,%mem", "--sort=-%cpu"],
                stderr=subprocess.DEVNULL
            ).decode().strip().split("\n")[1:]
            self.procs = []
            for line in result:
                parts = line.strip().split()
                if len(parts) >= 4:
                    self.procs.append({
                        "pid" : parts[0],
                        "name": parts[1][:14],
                        "cpu" : parts[2],
                        "mem" : parts[3]
                    })
            self.status = f"{len(self.procs)} processes"
        except Exception as e:
            self.status = f"Error: {e}"

    def kill(self, pid):
        try:
            subprocess.run(["kill", "-9", pid])
            self.status = f"Killed PID {pid}"
            self.refresh()
        except Exception as e:
            self.status = f"Error: {e}"

    def filtered_procs(self):
        if self.filter:
            return [p for p in self.procs if self.filter.lower() in p["name"].lower()]
        return self.procs

    def draw_list(self):
        self.screen.fill(BG)
        title = self.font.render("Process Killer", True, ACCENT)
        self.screen.blit(title, (8, 8))
        pygame.draw.line(self.screen, ACCENT, (0, 24), (240, 24), 1)

        color  = GREEN if "processes" in self.status else RED
        status = self.font.render(self.status, True, color)
        self.screen.blit(status, (8, 27))
        pygame.draw.line(self.screen, DIM, (0, 38), (240, 38), 1)

        header = self.font.render("PID    NAME           CPU  MEM", True, ACCENT)
        self.screen.blit(header, (8, 42))
        pygame.draw.line(self.screen, DIM, (0, 52), (240, 52), 1)

        procs = self.filtered_procs()
        y     = 56
        for i, proc in enumerate(procs[self.scroll:self.scroll + 9]):
            idx   = i + self.scroll
            color = ACCENT if idx == self.selected else TEXT
            if idx == self.selected:
                pygame.draw.rect(self.screen, (20, 40, 70), (4, y - 1, 232, 14), border_radius=3)
            pid  = self.font.render(proc["pid"][:6],  True, DIM)
            name = self.font.render(proc["name"],      True, color)
            cpu  = self.font.render(proc["cpu"] + "%", True, GREEN)
            mem  = self.font.render(proc["mem"] + "%", True, YELLOW)
            self.screen.blit(pid,  (8,   y))
            self.screen.blit(name, (48,  y))
            self.screen.blit(cpu,  (168, y))
            self.screen.blit(mem,  (205, y))
            y += 15

        if self.filter:
            filt = self.font.render(f"Filter: {self.filter}", True, YELLOW)
            self.screen.blit(filt, (8, 210))

        hint = self.font.render("R=refresh  K=kill  F=filter", True, DIM)
        self.screen.blit(hint, (8, 228))
        pygame.display.flip()

    def draw_filter(self):
        self.screen.fill(BG)
        title = self.font.render("Filter Process", True, ACCENT)
        self.screen.blit(title, (8, 8))
        pygame.draw.line(self.screen, ACCENT, (0, 24), (240, 24), 1)

        label = self.font.render("Filter by name:", True, GREEN)
        self.screen.blit(label, (8, 40))
        inp = self.font.render(f"{self.filter}_", True, TEXT)
        self.screen.blit(inp, (8, 58))

        hint = self.font.render("ENTER=apply  ESC=cancel", True, DIM)
        self.screen.blit(hint, (8, 228))
        pygame.display.flip()

    def draw(self):
        if self.mode == "list":
            self.draw_list()
        elif self.mode == "filter":
            self.draw_filter()

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if self.mode == "list":
                procs = self.filtered_procs()
                if event.key == pygame.K_DOWN:
                    if self.selected < len(procs) - 1:
                        self.selected += 1
                    if self.selected >= self.scroll + 9:
                        self.scroll += 1
                elif event.key == pygame.K_UP:
                    if self.selected > 0:
                        self.selected -= 1
                    if self.selected < self.scroll:
                        self.scroll -= 1
                elif event.key == pygame.K_r:
                    self.refresh()
                elif event.key == pygame.K_k:
                    if procs:
                        self.kill(procs[self.selected]["pid"])
                elif event.key == pygame.K_f:
                    self.mode   = "filter"
                    self.filter = ""

            elif self.mode == "filter":
                if event.key == pygame.K_RETURN:
                    self.mode     = "list"
                    self.selected = 0
                    self.scroll   = 0
                elif event.key == pygame.K_BACKSPACE:
                    self.filter = self.filter[:-1]
                elif event.key == pygame.K_ESCAPE:
                    self.mode   = "list"
                    self.filter = ""
                else:
                    self.filter += event.unicode
