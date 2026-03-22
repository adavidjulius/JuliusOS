import pygame
import json
import os

BG     = (10, 10, 20)
TEXT   = (255, 255, 255)
ACCENT = (0, 200, 255)
GREEN  = (0, 255, 100)
DIM    = (80, 80,   80)
RED    = (255, 80,  80)

TODO_FILE = "julius_todo.json"

class Todo:
    def __init__(self, screen, font):
        self.screen   = screen
        self.font     = font
        self.tasks    = self.load()
        self.selected = 0
        self.mode     = "list"
        self.input    = ""
        self.scroll   = 0
        self.filter   = "all"

    def load(self):
        if os.path.exists(TODO_FILE):
            with open(TODO_FILE) as f:
                return json.load(f)
        return []

    def save(self):
        with open(TODO_FILE, "w") as f:
            json.dump(self.tasks, f)

    def filtered(self):
        if self.filter == "done":
            return [t for t in self.tasks if t["done"]]
        elif self.filter == "pending":
            return [t for t in self.tasks if not t["done"]]
        return self.tasks

    def draw_list(self):
        self.screen.fill(BG)
        title = self.font.render("Todo List", True, ACCENT)
        self.screen.blit(title, (8, 8))

        total   = len(self.tasks)
        done    = len([t for t in self.tasks if t["done"]])
        counter = self.font.render(f"{done}/{total}", True, GREEN)
        self.screen.blit(counter, (200, 8))
        pygame.draw.line(self.screen, ACCENT, (0, 24), (240, 24), 1)

        filt = self.font.render(f"Filter: {self.filter}", True, DIM)
        self.screen.blit(filt, (8, 27))
        pygame.draw.line(self.screen, DIM, (0, 38), (240, 38), 1)

        tasks = self.filtered()
        if not tasks:
            msg = self.font.render("No tasks. Press N to add", True, DIM)
            self.screen.blit(msg, (8, 120))
        else:
            y = 42
            for i, task in enumerate(tasks[self.scroll:self.scroll + 10]):
                idx   = i + self.scroll
                color = ACCENT if idx == self.selected else TEXT
                if idx == self.selected:
                    pygame.draw.rect(self.screen, (20, 40, 70), (4, y - 1, 232, 15), border_radius=4)
                check = "[X]" if task["done"] else "[ ]"
                chcol = GREEN if task["done"] else DIM
                ch    = self.font.render(check, True, chcol)
                lb    = self.font.render(task["text"][:22], True, color)
                self.screen.blit(ch, (8,  y))
                self.screen.blit(lb, (40, y))
                y += 16

        hint = self.font.render("N=add ENTER=done D=del F=filter", True, DIM)
        self.screen.blit(hint, (8, 228))
        pygame.display.flip()

    def draw_add(self):
        self.screen.fill(BG)
        title = self.font.render("New Task", True, ACCENT)
        self.screen.blit(title, (8, 8))
        pygame.draw.line(self.screen, ACCENT, (0, 24), (240, 24), 1)

        label = self.font.render("Task:", True, GREEN)
        self.screen.blit(label, (8, 40))
        inp = self.font.render(f"{self.input}_", True, TEXT)
        self.screen.blit(inp, (8, 60))

        hint = self.font.render("ENTER=save  ESC=cancel", True, DIM)
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
                tasks = self.filtered()
                if event.key == pygame.K_DOWN:
                    if self.selected < len(tasks) - 1:
                        self.selected += 1
                    if self.selected >= self.scroll + 10:
                        self.scroll += 1
                elif event.key == pygame.K_UP:
                    if self.selected > 0:
                        self.selected -= 1
                    if self.selected < self.scroll:
                        self.scroll -= 1
                elif event.key == pygame.K_n:
                    self.mode  = "add"
                    self.input = ""
                elif event.key == pygame.K_RETURN:
                    if tasks:
                        tasks[self.selected]["done"] = not tasks[self.selected]["done"]
                        self.save()
                elif event.key == pygame.K_d:
                    if tasks:
                        self.tasks.remove(tasks[self.selected])
                        self.selected = max(0, self.selected - 1)
                        self.save()
                elif event.key == pygame.K_f:
                    cycle = {"all": "pending", "pending": "done", "done": "all"}
                    self.filter   = cycle[self.filter]
                    self.selected = 0
                    self.scroll   = 0

            elif self.mode == "add":
                if event.key == pygame.K_RETURN and self.input:
                    self.tasks.append({"text": self.input, "done": False})
                    self.save()
                    self.mode  = "list"
                    self.input = ""
                elif event.key == pygame.K_BACKSPACE:
                    self.input = self.input[:-1]
                elif event.key == pygame.K_ESCAPE:
                    self.mode  = "list"
                    self.input = ""
                else:
                    self.input += event.unicode
