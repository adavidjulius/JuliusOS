import pygame
import math

BG     = (8,   8,  18)
CARD   = (28,  28,  34)
WHITE  = (255, 255, 255)
DIM    = (100, 100, 110)
ACCENT = (0,  200, 255)
BLUE   = (10, 132, 255)

class AppFolder:
    def __init__(self, name, apps, color=(40,40,50)):
        self.name   = name
        self.apps   = apps
        self.color  = color
        self.page   = 0
        self.is_folder = True

    def get_preview_apps(self):
        return self.apps[:4]

class FolderManager:
    def __init__(self, screen, W, H, draw_icon_func):
        self.screen      = screen
        self.W           = W
        self.H           = H
        self.draw_icon   = draw_icon_func
        self.open_folder = None
        self.visible     = False
        self.font        = pygame.font.SysFont("helvetica", 14, bold=True)
        self.font_small  = pygame.font.SysFont("helvetica", 11)
        self.font_label  = pygame.font.SysFont("helvetica", 10)
        self.anim        = 0.0

    def open(self, folder):
        self.open_folder = folder
        self.visible     = True
        self.anim        = 0.0

    def close(self):
        self.visible     = False
        self.open_folder = None

    def rr(self, color, rect, radius):
        x, y, w, h = rect
        r = min(radius, w//2, h//2)
        pygame.draw.rect(self.screen, color, (x+r, y, w-2*r, h))
        pygame.draw.rect(self.screen, color, (x, y+r, w, h-2*r))
        for cx, cy in [(x+r,y+r),(x+w-r,y+r),(x+r,y+h-r),(x+w-r,y+h-r)]:
            pygame.draw.circle(self.screen, color, (cx,cy), r)

    def draw_folder_icon(self, surf, folder, x, y, size=60):
        r   = size//6
        self.rr(folder.color, (x, y, size, size), r)

        preview = folder.get_preview_apps()
        mini    = size//2 - 4
        offsets = [(2,2),(mini+4,2),(2,mini+4),(mini+4,mini+4)]

        for i, app in enumerate(preview[:4]):
            if i >= len(offsets):
                break
            ox, oy = offsets[i]
            self.rr(app["bg"],
                (x+ox, y+oy, mini, mini), mini//4)

        lbl = self.font_label.render(
            folder.name[:8], True, (*WHITE, 200))
        surf.blit(lbl,
            (x+size//2-lbl.get_width()//2, y+size+2))

    def draw(self):
        if not self.visible or not self.open_folder:
            return

        self.anim = min(1.0, self.anim + 0.08)
        scale     = 0.3 + 0.7 * self.anim
        alpha     = int(self.anim * 255)

        panel_w = int(self.W * 0.9 * scale)
        panel_h = int(self.H * 0.65 * scale)
        px      = (self.W - panel_w) // 2
        py      = (self.H - panel_h) // 2

        overlay = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, int(180 * self.anim)))
        self.screen.blit(overlay, (0,0))

        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel.fill((28, 28, 36, alpha))
        self.screen.blit(panel, (px, py))
        pygame.draw.rect(self.screen, (50,50,60),
            (px, py, panel_w, panel_h), 1, border_radius=20)

        # Folder name
        title = self.font.render(
            self.open_folder.name, True, (*WHITE, alpha))
        self.screen.blit(title,
            (self.W//2-title.get_width()//2, py+14))

        pygame.draw.line(self.screen, (50,50,60),
            (px, py+36), (px+panel_w, py+36), 1)

        # Apps grid
        apps    = self.open_folder.apps
        cols    = 4
        pad     = 12
        icon_sz = (panel_w - pad*(cols+1)) // cols
        start_y = py + 44

        self.folder_app_rects = []
        for i, app in enumerate(apps):
            col2 = i % cols
            row2 = i // cols
            ix   = px + pad + col2*(icon_sz+pad)
            iy   = start_y + row2*(icon_sz+18+6)

            if iy + icon_sz > py + panel_h - 10:
                break

            self.draw_icon(self.screen, app, ix, iy, icon_sz)
            lbl = self.font_label.render(
                app["name"], True, (*WHITE, alpha))
            self.screen.blit(lbl,
                (ix+icon_sz//2-lbl.get_width()//2,
                 iy+icon_sz+2))
            self.folder_app_rects.append(
                (ix, iy, icon_sz, icon_sz, app["name"]))

        hint = self.font_small.render(
            "Tap app to open  |  Swipe down to close",
            True, (*DIM, alpha))
        self.screen.blit(hint,
            (self.W//2-hint.get_width()//2,
             py+panel_h-18))

    def handle_touch(self, pos, is_swipe_down=False):
        if not self.visible:
            return None
        if is_swipe_down:
            self.close()
            return "closed"
        if hasattr(self, "folder_app_rects"):
            for rx,ry,rw,rh,name in self.folder_app_rects:
                if rx<=pos[0]<=rx+rw and ry<=pos[1]<=ry+rh:
                    self.close()
                    return name
        return None
