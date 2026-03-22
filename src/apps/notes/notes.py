
import pygame
import os
import json

BG     = (10, 10, 20)
TEXT   = (255, 255, 255)
ACCENT = (0, 200, 255)
GREEN  = (0, 255, 100)
DIM    = (80, 80,   80)
RED    = (255, 80,  80)
YELLOW = (255, 200,  0)

NOTES_FILE = "julius_notes.json"

class Notes:
    def __init__(self, screen, font):
        self.screen   = screen
        self.font     = font
        self.notes    = self.load()
        self.mode     = "list"
        self.selected = 0
        self.editing  = ""
        self.title    = ""
        self.stage    = "title"
        self.scroll   = 0

    def load(self):
        if os.path.exists(NOTES_FILE):
            with open(NOTES_FILE) as f:
                return json.load(f)
        return []

    def save(self):
        with open(NOTES_FILE, "w") as f:
            json.dump(self.notes, f)

    def draw_list(self):
        self.screen.fill(BG)
        title = self.font.render("Notes", True, ACCENT)
        self.screen.blit(title, (8, 8))
        count = self.font.render(f"{len(self.notes)} notes", True, DIM)
        self.screen.blit(count, (180, 8))
        pygame.draw.line(self.screen, ACCENT, (0, 24), (240, 24), 1)

        if not self.notes:
            msg = self.font.render("No notes. Press N to create", True, DIM)
            self.screen.blit(msg, (8, 120))
        else:
            y = 30
            for i, note in enumerate(self.notes[self.scroll:self.scroll + 12]):
                idx   = i + self.scroll
                color = ACCENT if idx == self.selected else TEXT
                if idx == self.selected:
                    pygame.draw.rect(self.screen, (20, 40, 70), (4, y - 1, 232, 15), border_radius=4)
                t = self.font.render(note["title"][:26], True, color)
                self.screen.blit(t, (8, y))
                y += 16

        hint = self.font.render("N=new  ENTER=open  D=del", True, DIM)
        self.screen.blit(hint, (8, 228))
        pygame.display.flip()

    def draw_edit(self):
        self.screen.fill(BG)
        if self.stage == "title":
            label = self.font.render("Note Title:", True, ACCENT)
            self.screen.blit(label, (8, 8))
            pygame.draw.line(self.screen, ACCENT, (0, 24), (240, 24), 1)
            inp = self.font.render(f"{self.title}_", True, TEXT)
            self.screen.blit(inp, (8, 40))
        elif self.stage == "body":
            label = self.font.render(self.title[:26], True, ACCENT)
            self.screen.blit(label, (8, 8))
            pygame.draw.line(self.screen, ACCENT, (0, 24), (240, 24), 1)
            lines = self.editing.split("\n")
            y     = 30
            for line in lines[-12:]:
                surf = self.font.render(line[:30], True, TEXT)
                self.screen.blit(surf, (8, y))
                y += 16
            cursor = self.font.render("_", True, GREEN)
            self.screen.blit(cursor, (8, y))

        hint = self.font.render("ENTER=newline  ESC=save", True, DIM)
        self.screen.blit(hint, (8, 228))
        pygame.display.flip()

    def draw_view(self):
        self.screen.fill(BG)
        note  = self.notes[self.selected]
        title = self.font.render(note["title"][:26], True, ACCENT)
        self.screen.blit(title, (8, 8))
        pygame.draw.line(self.screen, ACCENT, (0, 24), (240, 24), 1)

        lines = note["body"].split("\n")
        y     = 30
        for line in lines[self.scroll:self.scroll + 12]:
            surf = self.font.render(line[:30], True, TEXT)
            self.screen.blit(surf, (8, y))
            y += 16

        self.screen.blit(hint, (8, 228))
        pygame.display.flip()

    def draw(self):
        if self.mode == "list":
            self.draw_list()
        elif self.mode == "edit":
            self.draw_edit()
        elif self.mode == "view":
            self.draw_view()

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if self.mode == "list":
                if event.key == pygame.K_n:
                    self.mode   = "edit"
                    self.stage  = "title"
                    self.title  = ""
                    self.editing = ""
                elif event.key == pygame.K_DOWN:
                    if self.selected < len(self.notes) - 1:
                        self.selected += 1
                    if self.selected >= self.scroll + 12:
                        self.scroll += 1
                elif event.key == pygame.K_UP:
                    if self.selected > 0:
                        self.selected -= 1
                    if self.selected < self.scroll:
                        self.scroll -= 1
                elif event.key == pygame.K_RETURN:
                    if self.notes:
                        self.mode   = "view"
                        self.scroll = 0
                elif event.key == pygame.K_d:
                    if self.notes:
                        self.notes.pop(self.selected)
                        self.selected = max(0, self.selected - 1)
                        self.save()

            elif self.mode == "edit":
                if self.stage == "title":
                    if event.key == pygame.K_RETURN and self.title:
                        self.stage = "body"
                    elif event.key == pygame.K_BACKSPACE:
                        self.title = self.title[:-1]
                    elif event.key == pygame.K_ESCAPE:
                        self.mode  = "list"
                    else:
                        self.title += event.unicode
                elif self.stage == "body":
                    if event.key == pygame.K_ESCAPE:
                        self.notes.append({
                            "title": self.title,
                            "body" : self.editing
                        })
                        self.save()
                        self.mode  = "list"
                        self.stage = "title"
                    elif event.key == pygame.K_RETURN:
                        self.editing += "\n"
                    elif event.key == pygame.K_BACKSPACE:
                        self.editing = self.editing[:-1]
                    else:
                        self.editing += event.unicode

            elif self.mode == "view":
                note  = self.notes[self.selected]
                lines = note["body"].split("\n")
                if event.key == pygame.K_ESCAPE:
                    self.mode   = "list"
                    self.scroll = 0
                elif event.key == pygame.K_DOWN:
                    if self.scroll < len(lines) - 12:
                        self.scroll += 1
                elif event.key == pygame.K_UP:
                    if self.scroll > 0:
                        self.scroll -= 1
                elif event.key == pygame.K_e:
                    self.mode    = "edit"
                    self.stage   = "body"
                    self.title   = note["title"]
                    self.editing = note["body"]
                    self.notes.pop(self.selected)
