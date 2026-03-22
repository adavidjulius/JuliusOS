import pygame
import time

def boot_screen(screen):
    WIDTH, HEIGHT = 240, 240
    BG     = (10, 10, 20)
    ACCENT = (0, 200, 255)
    TEXT   = (255, 255, 255)
    DIM    = (50, 50, 80)

    font_title = pygame.font.SysFont("monospace", 22, bold=True)
    font_sub   = pygame.font.SysFont("monospace", 10)
    font_small = pygame.font.SysFont("monospace", 9)

    for alpha in range(0, 255, 5):
        screen.fill(BG)
        title = font_title.render("Julius OS", True, ACCENT)
        title.set_alpha(alpha)
        screen.blit(title, ((WIDTH - title.get_width()) // 2, 85))
        tag = font_sub.render("Built for control.", True, TEXT)
        tag.set_alpha(alpha)
        screen.blit(tag, ((WIDTH - tag.get_width()) // 2, 112))
        pygame.display.flip()
        time.sleep(0.01)

    messages = [
        "Initializing kernel...",
        "Loading drivers...",
        "Starting services...",
        "Mounting filesystem...",
        "Loading Julius OS...",
    ]

    for msg in messages:
        screen.fill(BG)
        title = font_title.render("Julius OS", True, ACCENT)
        screen.blit(title, ((WIDTH - title.get_width()) // 2, 85))
        tag = font_sub.render("Built for control.", True, TEXT)
        screen.blit(tag, ((WIDTH - tag.get_width()) // 2, 112))
        for prev_msg in messages[:messages.index(msg) + 1]:
            color = DIM if prev_msg != msg else TEXT
            surf  = font_small.render(prev_msg, True, color)
            idx   = messages.index(prev_msg)
            screen.blit(surf, (20, 160 + idx * 13))
        pygame.display.flip()
        time.sleep(0.3)

    for i in range(0, WIDTH - 40, 4):
        screen.fill(BG)
        title = font_title.render("Julius OS", True, ACCENT)
        screen.blit(title, ((WIDTH - title.get_width()) // 2, 85))
        tag = font_sub.render("Built for control.", True, TEXT)
        screen.blit(tag, ((WIDTH - tag.get_width()) // 2, 112))
        for idx, m in enumerate(messages):
            surf = font_small.render(m, True, DIM)
            screen.blit(surf, (20, 160 + idx * 13))
        pygame.draw.rect(screen, DIM,    (20, 225, WIDTH - 40, 6), border_radius=3)
        pygame.draw.rect(screen, ACCENT, (20, 225, i, 6),          border_radius=3)
        pygame.display.flip()
        time.sleep(0.01)

    time.sleep(0.3)
