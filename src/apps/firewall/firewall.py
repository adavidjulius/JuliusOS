import pygame
import subprocess
import threading

BG     = (10, 10, 20)
TEXT   = (255, 255, 255)
ACCENT = (0, 200, 255)
GREEN  = (0, 255, 100)
DIM    = (80, 80,   80)
RED    = (255, 80,  80)
YELLOW = (255, 200,  0)

class Firewall:
    def __init__(self, screen, font):
        self.screen   = screen
        self.font     = font
        self.rules    = []
        self.selected = 0
        self.scroll   = 0
        self.status   = "Press R to load rules"
        self.mode     = "list"
        self.input    = ""
        self.port_in  = ""
        self.proto_in = "tcp"
        self.action   = "ACCEPT"
        self.stage    = "port"

    def load_rules(self):
        try:
            result = subprocess.check_output(
                ["iptables", "-L", "INPUT", "-n", "--line-numbers"],
                stderr=subprocess.DEVNULL
            ).decode()
            self.rules  = []
            for line in result.strip().split("\n")[2:]:
                parts = line.strip().split()
                if len(parts) >= 4:
                    self.rules.append({
                        "num"   : parts[0],
                        "target": parts[1],
                        "proto" : parts[2],
                        "source": parts[4] if len(parts) > 4 else "any"
                    })
            self.status = f"{len(self.rules)} rules loaded"
        except Exception as e:
            self.status = f"Error: {e}"

    def add_rule(self, port, proto, action):
        try:
            subprocess.run([
                "iptables", "-A", "INPUT",
                "-p", proto,
                "--dport", port,
                "-j", action
            ], check=True)
            self.status = f"Rule added: {action} {proto}/{port}"
            self.load_rules()
        except Exception as e:
            self.status = f"Error: {e}"

    def delete_rule(self, num):
        try:
            subprocess.run([
                "iptables", "-D", "INPUT", num
            ], check=True)
            self.status = f"Rule {num} deleted"
            self.load_rules()
        except Exception as e:
            self.status = f"Error: {e}"

    def draw_list(self):
        self.screen.fill(BG)
        title = self.font.render("Firewall", True, ACCENT)
        self.screen.blit(title, (8, 8))
        pygame.draw.line(self.screen, ACCENT, (0, 24), (240, 24), 1)

        color  = GREEN if "loaded" in self.status else RED
        status = self.font.render(self.status[:30], True, color)
        self.screen.blit(status, (8, 27))
        pygame.draw.line(self.screen, DIM, (0, 38), (240, 38), 1)

        header = self.font.render("NUM  TARGET    PROTO  SRC", True, ACCENT)
        self.screen.blit(header, (8, 42))
        pygame.draw.line(self.screen, DIM, (0, 52), (240, 52), 1)

        y = 56
        for i, rule in enumerate(self.rules[self.scroll:self.scroll + 9]):
            idx   = i + self.scroll
            color = ACCENT if idx == self.selected else TEXT
            if idx == self.selected:
                pygame.draw.rect(self.screen, (20, 40, 70), (4, y - 1, 232, 14), border_radius=3)
            num    = self.font.render(rule["num"][:3],    True, DIM)
            target = self.font.render(rule["target"][:8], True, GREEN if rule["target"] == "ACCEPT" else RED)
            proto  = self.font.render(rule["proto"][:5],  True, YELLOW)
            src    = self.font.render(rule["source"][:10],True, color)
            self.screen.blit(num,    (8,   y))
            self.screen.blit(target, (32,  y))
            self.screen.blit(proto,  (112, y))
            self.screen.blit(src,    (160, y))
            y += 15

        if not self.rules:
            msg = self.font.render("No rules. Press A to add", True, DIM)
            self.screen.blit(msg, (8, 100))

        hint = self.font.render("R=load  A=add  D=delete", True, DIM)
        self.screen.blit(hint, (8, 228))
        pygame.display.flip()

    def draw_add(self):
        self.screen.fill(BG)
        title = self.font.render("Add Rule", True, ACCENT)
        self.screen.blit(title, (8, 8))
        pygame.draw.line(self.screen, ACCENT, (0, 24), (240, 24), 1)

        stages = [
            ("Port",     self.port_in,  "port"),
            ("Protocol", self.proto_in, "proto"),
            ("Action",   self.action,   "action"),
        ]
        y = 36
        for label, val, stage in stages:
            color = GREEN if self.stage == stage else DIM
            lb    = self.font.render(f"{label}:", True, color)
            vl    = self.font.render(str(val),    True, TEXT)
            self.screen.blit(lb, (8,   y))
            self.screen.blit(vl, (100, y))
            y += 24

        hint = self.font.render("ENTER=next  ESC=cancel", True, DIM)
        self.screen.blit(hint, (8, 228))
        pygame.display.flip()

    def draw(self):
        if self.mode == "list":
            self.draw_list()
        elif self.mode == "add":
            self.draw_add()

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if self.mode == "list":
                if event.key == pygame.K_DOWN:
                    if self.selected < len(self.rules) - 1:
                        self.selected += 1
                    if self.selected >= self.scroll + 9:
                        self.scroll += 1
                elif event.key == pygame.K_UP:
                    if self.selected > 0:
                        self.selected -= 1
                    if self.selected < self.scroll:
                        self.scroll -= 1
                elif event.key == pygame.K_r:
                    self.load_rules()
                elif event.key == pygame.K_a:
                    self.mode     = "add"
                    self.stage    = "port"
                    self.port_in  = ""
                    self.proto_in = "tcp"
                    self.action   = "ACCEPT"
                elif event.key == pygame.K_d:
                    if self.rules:
                        self.delete_rule(self.rules[self.selected]["num"])

            elif self.mode == "add":
                if event.key == pygame.K_RETURN:
                    if self.stage == "port" and self.port_in:
                        self.stage = "proto"
                    elif self.stage == "proto":
                        self.stage = "action"
                    elif self.stage == "action":
                        self.add_rule(self.port_in, self.proto_in, self.action)
                        self.mode = "list"
                elif event.key == pygame.K_BACKSPACE:
                    if self.stage == "port":
                        self.port_in = self.port_in[:-1]
                elif event.key == pygame.K_ESCAPE:
                    self.mode = "list"
                elif event.key == pygame.K_t and self.stage == "proto":
                    self.proto_in = "tcp"
                elif event.key == pygame.K_u and self.stage == "proto":
                    self.proto_in = "udp"
                elif event.key == pygame.K_a and self.stage == "action":
                    self.action = "ACCEPT"
                elif event.key == pygame.K_d and self.stage == "action":
                    self.action = "DROP"
                else:
                    if self.stage == "port":
                        self.port_in += event.unicode
