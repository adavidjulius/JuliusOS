import pygame
import socket
import threading

BG     = (10, 10, 20)
TEXT   = (255, 255, 255)
ACCENT = (0, 200, 255)
GREEN  = (0, 255, 100)
DIM    = (80, 80,   80)
RED    = (255, 80,  80)

class SSHClient:
    def __init__(self, screen, font):
        self.screen  = screen
        self.font    = font
        self.log     = ["Julius SSH Client v0.3"]
        self.input   = ""
        self.host    = ""
        self.user    = ""
        self.stage   = "host"
        self.status  = "Enter host IP"

    def draw(self):
        self.screen.fill(BG)
        title = self.font.render("SSH Client", True, ACCENT)
        self.screen.blit(title, (8, 8))
        pygame.draw.line(self.screen, ACCENT, (0, 24), (240, 24), 1)

        status = self.font.render(self.status, True, GREEN)
        self.screen.blit(status, (8, 28))
        pygame.draw.line(self.screen, DIM, (0, 40), (240, 40), 1)

        y = 46
        for line in self.log[-10:]:
            surf = self.font.render(line[:30], True, TEXT)
            self.screen.blit(surf, (8, y))
            y += 17

        inp = self.font.render(f"> {self.input}_", True, GREEN)
        self.screen.blit(inp, (8, 210))

        hint = self.font.render("ENTER=confirm  ESC=clear", True, DIM)
        self.screen.blit(hint, (8, 228))
        pygame.display.flip()

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                if self.stage == "host":
                    self.host   = self.input
                    self.input  = ""
                    self.stage  = "user"
                    self.log.append(f"Host: {self.host}")
                elif self.stage == "user":
                    self.user   = self.input
                    self.input  = ""
                    self.stage  = "ready"
                    self.status = f"ssh {self.user}@{self.host}"
                    self.log.append(f"User: {self.user}")
                    self.log.append(f"Run: ssh {self.user}@{self.host}")
                    self.log.append("Use terminal app to connect")
            elif event.key == pygame.K_BACKSPACE:
                self.input = self.input[:-1]
            elif event.key == pygame.K_ESCAPE:
                self.input  = ""
                self.host   = ""
                self.user   = ""
                self.stage  = "host"
                self.status = "Enter host IP"
                self.log    = ["Julius SSH Client v0.3"]
            else:
                self.input += event.unicode
