import pygame
import os

BG     = (10, 10, 20)
TEXT   = (255, 255, 255)
ACCENT = (0, 200, 255)
GREEN  = (0, 255, 100)
DIM    = (80, 80,   80)
RED    = (255, 80,  80)
CURSOR = (0, 255, 100)

class TextEditor:
    def __init__(self, screen, font):
        self.screen   = screen
        self.font     = font
        self.lines    = [""]
        self.cursor_x = 0
        self.cursor_y = 0
        self.scroll   = 0
        self.filename = ""
        self.mode     = "input_name"
        self.status   = "Enter filename"
        self.modified = False

    def current_line(self):
        return self.lines[self.cursor_y]

    def insert_char(self, ch):
        line = self.lines[self.cursor_y]
        self.lines[self.cursor_y] = line[:self.cursor_x] + ch + line[self.cursor_x:]
        self.cursor_x  += 1
        self.modified   = True

    def backspace(self):
        if self.cursor_x > 0:
            line = self.lines[self.cursor_y]
            self.lines[self.cursor_y] = line[:self.cursor_x - 1] + line[self.cursor_x:]
            self.cursor_x -= 1
            self.modified  = True
        elif self.cursor_y > 0:
            prev = self.lines[self.cursor_y - 1]
            self.cursor_x = len(prev)
            self.lines[self.cursor_y - 1] += self.lines[self.cursor_y]
            self.lines.pop(self.cursor_y)
            self.cursor_y -= 1
            self.modified  = True

    def newline(self):
        line = self.lines[self.cursor_y]
        self.lines[self.cursor_y]       = line[:self.cursor_x]
        self.lines.insert(self.cursor_y + 1, line[self.cursor_x:])
        self.cursor_y += 1
        self.cursor_x  = 0
        self.modified  = True

    def save(self):
        try:
            with open(self.filename, "w") as f:
                f.write("\n".join(self.lines))
            self.status   = f"Saved {self.filename}"
            self.modified = False
        except Exception as e:
            self.status = f"Error: {e}"

    def load(self):
        try:
            if os.path.exists(self.filename):
                with open(self.filename) as f:
                    self.lines = f.read().split("\n")
                self.status = f"Opened {self.filename}"
            else:
                self.lines  = [""]
                self.status = f"New file: {self.filename}"
            self.cursor_x = 0
            self.cursor_y = 0
            self.mode     = "edit"
        except Exception as e:
            self.status = f"Error: {e}"

    def draw_input_name(self):
        self.screen.fill(BG)
        title = self.font.render("Text Editor", True, ACCENT)
        self.screen.blit(title, (8, 8))
        pygame.draw.line(self.screen, ACCENT, (0, 24), (240, 24), 1)

        label = self.font.render("Filename:", True, GREEN)
        self.screen.blit(label, (8, 40))
        inp = self.font.render(f"{self.filename}_", True, TEXT)
        self.screen.blit(inp, (8, 58))

        hint = self.font.render("ENTER=open/create  ESC=cancel", True, DIM)
        self.screen.blit(hint, (8, 228))
        pygame.display.flip()

    def draw_edit(self):
        self.screen.fill(BG)

        fname = self.filename[-20:] + (" *" if self.modified else "")
        title = self.font.render(fname, True, ACCENT)
        self.screen.blit(title, (8, 8))
        pygame.draw.line(self.screen, ACCENT, (0, 24), (240, 24), 1)

        visible = self.lines[self.scroll:self.scroll + 13]
        y       = 28
        for i, line in enumerate(visible):
            row = i + self.scroll
            if row == self.cursor_y:
                pygame.draw.rect(self.screen, (20, 40, 70), (4, y - 1, 232, 13), border_radius=2)
            surf = self.font.render(line[:28], True, TEXT)
            self.screen.blit(surf, (8, y))

            if row == self.cursor_y:
                cx = 8 + self.cursor_x * 7
                pygame.draw.rect(self.screen, CURSOR, (cx, y, 2, 11))
            y += 14

        pos    = self.font.render(f"L{self.cursor_y + 1}:C{self.cursor_x + 1}", True, DIM)
        status = self.font.render(self.status[:20], True, GREEN)
        self.screen.blit(pos,    (8,   226))
        self.screen.blit(status, (60,  226))

        hint = self.font.render("CTRL+S=save  ESC=menu", True, DIM)
        self.screen.blit(hint, (8, 214))
        pygame.display.flip()

    def draw(self):
        if self.mode == "input_name":
            self.draw_input_name()
        elif self.mode == "edit":
            self.draw_edit()

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if self.mode == "input_name":
                if event.key == pygame.K_RETURN and self.filename:
                    self.load()
                elif event.key == pygame.K_BACKSPACE:
                    self.filename = self.filename[:-1]
                elif event.key == pygame.K_ESCAPE:
                    self.filename = ""
                else:
                    self.filename += event.unicode

            elif self.mode == "edit":
                mods = pygame.key.get_mods()
                if event.key == pygame.K_ESCAPE:
                    self.mode     = "input_name"
                    self.filename = ""
                    self.lines    = [""]
                    self.cursor_x = 0
                    self.cursor_y = 0
                elif event.key == pygame.K_s and mods & pygame.KMOD_CTRL:
                    self.save()
                elif event.key == pygame.K_RETURN:
                    self.newline()
                elif event.key == pygame.K_BACKSPACE:
                    self.backspace()
                elif event.key == pygame.K_LEFT:
                    self.cursor_x = max(0, self.cursor_x - 1)
                elif event.key == pygame.K_RIGHT:
                    self.cursor_x = min(len(self.current_line()), self.cursor_x + 1)
                elif event.key == pygame.K_UP:
                    if self.cursor_y > 0:
                        self.cursor_y -= 1
                        self.cursor_x = min(self.cursor_x, len(self.current_line()))
                    if self.cursor_y < self.scroll:
                        self.scroll -= 1
                elif event.key == pygame.K_DOWN:
                    if self.cursor_y < len(self.lines) - 1:
                        self.cursor_y += 1
                        self.cursor_x = min(self.cursor_x, len(self.current_line()))
                    if self.cursor_y >= self.scroll + 13:
                        self.scroll += 1
                elif event.unicode:
                    self.insert_char(event.unicode)
