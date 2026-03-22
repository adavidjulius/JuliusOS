import pygame
import json
import os
import hashlib

BG     = (10, 10, 20)
TEXT   = (255, 255, 255)
ACCENT = (0, 200, 255)
GREEN  = (0, 255, 100)
DIM    = (80, 80,   80)
RED    = (255, 80,  80)

PASS_FILE = "julius_passwords.json"

class PasswordManager:
    def __init__(self, screen, font):
        self.screen   = screen
        self.font     = font
        self.data     = self.load()
        self.selected = 0
        self.mode     = "list"
        self.scroll   = 0
        self.status   = ""
        self.inputs   = {"site": "", "user": "", "pass": ""}
        self.stage    = "site"
        self.show     = False

    def load(self):
        if os.path.exists(PASS_FILE):
            with open(PASS_FILE) as f:
                return json.load(f)
        return []

    def save(self):
        with open(PASS_FILE, "w") as f:
            json.dump(self.data, f)

    def mask(self, text):
        return "*" * len(text)

    def draw_list(self):
        self.screen.fill(BG)
        title = self.font.render("Passwords", True, ACCENT)
        self.screen.blit(title, (8, 8))
        count = self.font.render(f"{len(self.data)}", True, DIM)
        self.screen.blit(count, (210, 8))
        pygame.draw.line(self.screen, ACCENT, (0, 24), (240, 24), 1)

        if self.status:
            st = self.font.render(self.status, True, GREEN)
            self.screen.blit(st, (8, 27))
        pygame.draw.line(self.screen, DIM, (0, 38), (240, 38), 1)

        if not self.data:
            msg = self.font.render("No passwords. Press N to add", True, DIM)
            self.screen.blit(msg, (8, 120))
        else:
            y = 42
            for i, entry in enumerate(self.data[self.scroll:self.scroll + 9]):
                idx   = i + self.scroll
                color = ACCENT if idx == self.selected else TEXT
                if idx == self.selected:
                    pygame.draw.rect(self.screen, (20, 40, 70), (4, y - 1, 232, 26), border_radius=4)
                site = self.font.render(entry["site"][:18], True, color)
                user = self.font.render(entry["user"][:18], True, DIM)
                self.screen.blit(site, (8, y))
                self.screen.blit(user, (8, y + 13))
                y += 30

        hint = self.font.render("N=add  V=view  D=del", True, DIM)
        self.screen.blit(hint, (8, 228))
        pygame.display.flip()

    def draw_add(self):
        self.screen.fill(BG)
        title = self.font.render("Add Password", True, ACCENT)
        self.screen.blit(title, (8, 8))
        pygame.draw.line(self.screen, ACCENT, (0, 24), (240, 24), 1)

        labels = {"site": "Website/App:", "user": "Username:", "pass": "Password:"}
        y      = 40
        for key, label in labels.items():
            color = GREEN if key == self.stage else DIM
            lb    = self.font.render(label, True, color)
            self.screen.blit(lb, (8, y))
            val   = self.inputs[key]
            if key == "pass" and not self.show:
                val = self.mask(val)
            val  += "_" if key == self.stage else ""
            inp   = self.font.render(val[:26], True, TEXT)
            self.screen.blit(inp, (8, y + 14))
            y    += 40

        hint = self.font.render("ENTER=next  ESC=cancel", True, DIM)
        self.screen.blit(hint, (8, 228))
        pygame.display.flip()

    def draw_view(self):
        self.screen.fill(BG)
        entry = self.data[self.selected]
        title = self.font.render("View Password", True, ACCENT)
        self.screen.blit(title, (8, 8))
        pygame.draw.line(self.screen, ACCENT, (0, 24), (240, 24), 1)

        site = self.font.render(f"Site : {entry['site']}", True, TEXT)
        user = self.font.render(f"User : {entry['user']}", True, TEXT)
        pwd  = entry["pass"] if self.show else self.mask(entry["pass"])
        pasw = self.font.render(f"Pass : {pwd[:20]}",     True, GREEN)

        self.screen.blit(site, (8, 40))
        self.screen.blit(user, (8, 60))
        self.screen.blit(pasw, (8, 80))

        toggle = self.font.render(
            "H=hide" if self.show else "S=show password", True, DIM
        )
        self.screen.blit(toggle, (8, 110))

        hint = self.font.render("ESC=back", True, DIM)
        self.screen.blit(hint, (8, 228))
        pygame.display.flip()

    def draw(self):
        if self.mode == "list":
            self.draw_list()
        elif self.mode == "add":
            self.draw_add()
        elif self.mode == "view":
            self.draw_view()

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if self.mode == "list":
                if event.key == pygame.K_DOWN:
                    if self.selected < len(self.data) - 1:
                        self.selected += 1
                    if self.selected >= self.scroll + 9:
                        self.scroll += 1
                elif event.key == pygame.K_UP:
                    if self.selected > 0:
                        self.selected -= 1
                    if self.selected < self.scroll:
                        self.scroll -= 1
                elif event.key == pygame.K_n:
                    self.mode   = "add"
                    self.stage  = "site"
                    self.inputs = {"site": "", "user": "", "pass": ""}
                elif event.key == pygame.K_v:
                    if self.data:
                        self.mode = "view"
                        self.show = False
                elif event.key == pygame.K_d:
                    if self.data:
                        self.data.pop(self.selected)
                        self.selected = max(0, self.selected - 1)
                        self.save()
                        self.status = "Deleted"

            elif self.mode == "add":
                if event.key == pygame.K_RETURN:
                    if self.inputs[self.stage]:
                        order = ["site", "user", "pass"]
                        idx   = order.index(self.stage)
                        if idx < 2:
                            self.stage = order[idx + 1]
                        else:
                            self.data.append(dict(self.inputs))
                            self.save()
                            self.mode   = "list"
                            self.status = f"Saved {self.inputs['site']}"
                elif event.key == pygame.K_BACKSPACE:
                    self.inputs[self.stage] = self.inputs[self.stage][:-1]
                elif event.key == pygame.K_ESCAPE:
                    self.mode = "list"
                else:
                    self.inputs[self.stage] += event.unicode

            elif self.mode == "view":
                if event.key == pygame.K_ESCAPE:
                    self.mode = "list"
                elif event.key == pygame.K_s:
                    self.show = True
                elif event.key == pygame.K_h:
                    self.show = False
