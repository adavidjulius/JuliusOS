import pygame
import os
import shutil

BG     = (10, 10, 20)
TEXT   = (255, 255, 255)
ACCENT = (0, 200, 255)
GREEN  = (0, 255, 100)
RED    = (255, 80,  80)
DIM    = (80, 80,   80)
FOLDER = (255, 200,  0)

class FileManager:
    def __init__(self, screen, font):
        self.screen   = screen
        self.font     = font
        self.path     = os.path.expanduser("~")
        self.items    = []
        self.selected = 0
        self.scroll   = 0
        self.status   = ""
        self.clipboard = None
        self.refresh()

    def refresh(self):
        try:
            entries    = os.listdir(self.path)
            dirs       = sorted([e for e in entries if os.path.isdir(os.path.join(self.path, e))])
            files      = sorted([e for e in entries if os.path.isfile(os.path.join(self.path, e))])
            self.items = [".."] + dirs + files
        except Exception as e:
            self.status = str(e)
            self.items  = [".."]
        self.selected = 0
        self.scroll   = 0

    def current_item(self):
        if self.items:
            return self.items[self.selected]
        return None

    def full_path(self, name):
        return os.path.join(self.path, name)

    def enter(self):
        item = self.current_item()
        if not item:
            return
        if item == "..":
            self.path = os.path.dirname(self.path)
            self.refresh()
        elif os.path.isdir(self.full_path(item)):
            self.path = self.full_path(item)
            self.refresh()
        else:
            self.status = f"File: {item}"

    def delete(self):
        item = self.current_item()
        if item and item != "..":
            try:
                fp = self.full_path(item)
                if os.path.isdir(fp):
                    shutil.rmtree(fp)
                else:
                    os.remove(fp)
                self.status = f"Deleted {item}"
                self.refresh()
            except Exception as e:
                self.status = str(e)

    def copy(self):
        item = self.current_item()
        if item and item != "..":
            self.clipboard = self.full_path(item)
            self.status    = f"Copied {item}"

    def paste(self):
        if self.clipboard:
            name = os.path.basename(self.clipboard)
            dst  = os.path.join(self.path, name)
            try:
                if os.path.isdir(self.clipboard):
                    shutil.copytree(self.clipboard, dst)
                else:
                    shutil.copy2(self.clipboard, dst)
                self.status = f"Pasted {name}"
                self.refresh()
            except Exception as e:
                self.status = str(e)

    def draw(self):
        self.screen.fill(BG)
        title = self.font.render("File Manager", True, ACCENT)
        self.screen.blit(title, (8, 8))
        pygame.draw.line(self.screen, ACCENT, (0, 24), (240, 24), 1)

        path_label = self.font.render(self.path[-28:], True, DIM)
        self.screen.blit(path_label, (8, 27))
        pygame.draw.line(self.screen, DIM, (0, 38), (240, 38), 1)

        visible = self.items[self.scroll:self.scroll + 10]
        y       = 42
        for i, item in enumerate(visible):
            idx    = i + self.scroll
            color  = ACCENT if idx == self.selected else TEXT
            fp     = self.full_path(item)
            prefix = "/" if item != ".." and os.path.isdir(fp) else " "
            fcolor = FOLDER if prefix == "/" else color
            label  = self.font.render(f"{prefix}{item[:24]}", True, fcolor if idx == self.selected else fcolor)
            if idx == self.selected:
                pygame.draw.rect(self.screen, (20, 40, 70), (4, y - 1, 232, 15), border_radius=4)
            self.screen.blit(label, (8, y))
            y += 16

        if self.status:
            st = self.font.render(self.status[:30], True, GREEN)
            self.screen.blit(st, (8, 210))

        hint = self.font.render("ENTER  D=del  C=copy  V=paste", True, DIM)
        self.screen.blit(hint, (8, 228))
        pygame.display.flip()

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_DOWN:
                if self.selected < len(self.items) - 1:
                    self.selected += 1
                if self.selected >= self.scroll + 10:
                    self.scroll += 1
            elif event.key == pygame.K_UP:
                if self.selected > 0:
                    self.selected -= 1
                if self.selected < self.scroll:
                    self.scroll -= 1
            elif event.key == pygame.K_RETURN:
                self.enter()
            elif event.key == pygame.K_d:
                self.delete()
            elif event.key == pygame.K_c:
                self.copy()
            elif event.key == pygame.K_v:
                self.paste()
