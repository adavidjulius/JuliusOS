import pygame
import subprocess

BG   = (10, 10, 20)
TEXT = (0, 255, 100)

class Terminal:
    def __init__(self, screen, font):
        self.screen = screen
        self.font   = font
        self.lines  = ["Julius OS Terminal v0.1", "$ "]
        self.input  = ""

    def run_command(self, cmd):
        try:
            result = subprocess.check_output(
                cmd, shell=True, stderr=subprocess.STDOUT
            ).decode()
            self.lines += result.split("\n")
        except Exception as e:
            self.lines.append(f"Error: {str(e)}")
        self.lines.append("$ ")

    def draw(self):
        self.screen.fill(BG)
        y = 10
        for line in self.lines[-18:]:
            surf = self.font.render(line, True, TEXT)
            self.screen.blit(surf, (8, y))
            y += 13
        pygame.display.flip()

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self.run_command(self.input)
                self.input = ""
            elif event.key == pygame.K_BACKSPACE:
                self.input = self.input[:-1]
            else:
                self.input += event.unicode
            self.lines[-1] = f"$ {self.input}"
