import pygame
import subprocess
import threading
import socket

BG     = (10, 10, 20)
TEXT   = (255, 255, 255)
ACCENT = (0, 200, 255)
GREEN  = (0, 255, 100)
DIM    = (80, 80,   80)
RED    = (255, 80,  80)
YELLOW = (255, 200,  0)

TOOLS = ["Ping", "Traceroute", "DNS Lookup", "My IP", "Interfaces"]

class NetTools:
    def __init__(self, screen, font):
        self.screen   = screen
        self.font     = font
        self.selected = 0
        self.output   = []
        self.input    = ""
        self.mode     = "menu"
        self.status   = ""

    def run_ping(self, host):
        self.output = [f"Pinging {host}..."]
        def run():
            try:
                result = subprocess.check_output(
                    ["ping", "-c", "4", host],
                    stderr=subprocess.STDOUT
                ).decode()
                self.output += result.split("\n")
            except Exception as e:
                self.output.append(str(e))
        t = threading.Thread(target=run)
        t.daemon = True
        t.start()

    def run_traceroute(self, host):
        self.output = [f"Traceroute {host}..."]
        def run():
            try:
                result = subprocess.check_output(
                    ["traceroute", "-m", "10", host],
                    stderr=subprocess.STDOUT
                ).decode()
                self.output += result.split("\n")
            except Exception as e:
                self.output.append(str(e))
        t = threading.Thread(target=run)
        t.daemon = True
        t.start()

    def run_dns(self, host):
        self.output = [f"DNS: {host}"]
        try:
            result = socket.getaddrinfo(host, None)
            for r in result[:4]:
                self.output.append(str(r[4][0]))
        except Exception as e:
            self.output.append(str(e))

    def run_myip(self):
        self.output = ["My IP Addresses"]
        try:
            hostname = socket.gethostname()
            local    = socket.gethostbyname(hostname)
            self.output.append(f"Local  : {local}")
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            self.output.append(f"Network: {s.getsockname()[0]}")
            s.close()
        except Exception as e:
            self.output.append(str(e))

    def run_interfaces(self):
        self.output = ["Network Interfaces"]
        try:
            result = subprocess.check_output(
                ["ip", "addr"], stderr=subprocess.STDOUT
            ).decode()
            for line in result.split("\n"):
                if line.strip():
                    self.output.append(line.strip()[:30])
        except Exception as e:
            self.output.append(str(e))

    def execute(self):
        tool = TOOLS[self.selected]
        if tool in ["Ping", "Traceroute", "DNS Lookup"]:
            self.mode   = "input"
            self.input  = ""
            self.status = f"Enter host for {tool}:"
        elif tool == "My IP":
            self.mode = "output"
            self.run_myip()
        elif tool == "Interfaces":
            self.mode = "output"
            self.run_interfaces()

    def draw_menu(self):
        self.screen.fill(BG)
        title = self.font.render("Net Tools", True, ACCENT)
        self.screen.blit(title, (8, 8))
        pygame.draw.line(self.screen, ACCENT, (0, 24), (240, 24), 1)

        y = 32
        for i, tool in enumerate(TOOLS):
            color = ACCENT if i == self.selected else TEXT
            if i == self.selected:
                pygame.draw.rect(self.screen, (20, 40, 70), (4, y - 1, 232, 15), border_radius=4)
            label = self.font.render(tool, True, color)
            self.screen.blit(label, (8, y))
            y += 22

        hint = self.font.render("↑↓=select  ENTER=run", True, DIM)
        self.screen.blit(hint, (8, 228))
        pygame.display.flip()

    def draw_input(self):
        self.screen.fill(BG)
        title = self.font.render("Net Tools", True, ACCENT)
        self.screen.blit(title, (8, 8))
        pygame.draw.line(self.screen, ACCENT, (0, 24), (240, 24), 1)

        status = self.font.render(self.status, True, GREEN)
        self.screen.blit(status, (8, 30))
        inp = self.font.render(f"> {self.input}_", True, TEXT)
        self.screen.blit(inp, (8, 50))

        hint = self.font.render("ENTER=run  ESC=back", True, DIM)
        self.screen.blit(hint, (8, 228))
        pygame.display.flip()

    def draw_output(self):
        self.screen.fill(BG)
        title = self.font.render(TOOLS[self.selected], True, ACCENT)
        self.screen.blit(title, (8, 8))
        pygame.draw.line(self.screen, ACCENT, (0, 24), (240, 24), 1)

        y = 30
        for line in self.output[-12:]:
            surf = self.font.render(line[:30], True, TEXT)
            self.screen.blit(surf, (8, y))
            y += 17

        hint = self.font.render("ESC=back", True, DIM)
        self.screen.blit(hint, (8, 228))
        pygame.display.flip()

    def draw(self):
        if self.mode == "menu":
            self.draw_menu()
        elif self.mode == "input":
            self.draw_input()
        elif self.mode == "output":
            self.draw_output()

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if self.mode == "menu":
                if event.key == pygame.K_DOWN:
                    self.selected = (self.selected + 1) % len(TOOLS)
                elif event.key == pygame.K_UP:
                    self.selected = (self.selected - 1) % len(TOOLS)
                elif event.key == pygame.K_RETURN:
                    self.execute()

            elif self.mode == "input":
                if event.key == pygame.K_RETURN and self.input:
                    self.mode = "output"
                    tool      = TOOLS[self.selected]
                    if tool == "Ping":
                        self.run_ping(self.input)
                    elif tool == "Traceroute":
                        self.run_traceroute(self.input)
                    elif tool == "DNS Lookup":
                        self.run_dns(self.input)
                elif event.key == pygame.K_BACKSPACE:
                    self.input = self.input[:-1]
                elif event.key == pygame.K_ESCAPE:
                    self.mode  = "menu"
                else:
                    self.input += event.unicode

            elif self.mode == "output":
                if event.key == pygame.K_ESCAPE:
                    self.mode   = "menu"
                    self.output = []
