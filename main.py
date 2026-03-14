import pygame
import sys
import random
from modules.flashlight import Flashlight
from modules.camera import Camera
from modules.startBackgroudMusic import AudioManager
from modules.orario import Orario

pygame.init()
WIDTH, HEIGHT = 1280, 720
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Five Nights at School")
clock = pygame.time.Clock()
orologio = Orario()
base_background = pygame.image.load("assets/images/ufficio.jpg").convert()
menu_background = pygame.transform.scale(base_background, (WIDTH, HEIGHT))
game_background = pygame.transform.scale(base_background, (int(WIDTH * 1.7), HEIGHT))

flashlight = Flashlight(WIDTH, HEIGHT, radius=120, alpha=200)
camera = Camera(WIDTH, game_background.get_width(), smoothing=0.13)
audiomanager = AudioManager()

font_title = pygame.font.SysFont(None, 96)
font_button = pygame.font.SysFont(None, 56)
font_night = pygame.font.SysFont(None, 92)
font_hour = pygame.font.SysFont(None, 68)

button_width, button_height = 280, 80
play_button = pygame.Rect((WIDTH - button_width) // 2, HEIGHT // 2 - 20, button_width, button_height)
exit_button = pygame.Rect((WIDTH - button_width) // 2, HEIGHT // 2 + 90, button_width, button_height)

MENU_MUSIC = "assets/audio/menu.wav"
BUTTON_SOUND = "assets/audio/pulsanti.wav"
INTRO_DURATION_MS = 2600
MUSIC_FADE_MS = 800

in_menu_music = audiomanager.play_music(music_file=MENU_MUSIC)
state = "menu"
current_night = 1
intro_start_time = 0


def enter_game():
    global state, intro_start_time
    audiomanager.play_sound(BUTTON_SOUND, volume=0.8)
    audiomanager.stop_music(fade_ms=MUSIC_FADE_MS)
    intro_start_time = pygame.time.get_ticks()
    state = "night_intro"


def enter_menu(play_click=False):
    global state
    if play_click:
        audiomanager.play_sound(BUTTON_SOUND, volume=0.8)
    audiomanager.play_music(music_file=MENU_MUSIC, fade_ms=MUSIC_FADE_MS)
    state = "menu"

def draw_button(rect, text):
    mouse_pos = pygame.mouse.get_pos()
    hovered = rect.collidepoint(mouse_pos)
    color = (210, 210, 210) if hovered else (170, 170, 170)

    pygame.draw.rect(screen, color, rect, border_radius=14)
    pygame.draw.rect(screen, (40, 40, 40), rect, width=3, border_radius=14)

    label = font_button.render(text, True, (25, 25, 25))
    label_rect = label.get_rect(center=rect.center)
    screen.blit(label, label_rect)


def draw_glitch_menu_overlay(surface):
    # Scanlines leggere per un look CRT costante.
    scanlines = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    for y in range(0, HEIGHT, 4):
        pygame.draw.line(scanlines, (0, 0, 0, 24), (0, y), (WIDTH, y))
    surface.blit(scanlines, (0, 0))

    if random.random() > 0.16:
        return

    snapshot = surface.copy()

    # Distorsioni orizzontali a strisce come salto video.
    for _ in range(random.randint(6, 16)):
        y = random.randint(0, HEIGHT - 6)
        h = random.randint(2, 10)
        shift = random.randint(-45, 45)
        src = pygame.Rect(0, y, WIDTH, h)
        surface.blit(snapshot, (shift, y), src)

    # Statico granulare veloce.
    noise = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    for _ in range(240):
        x = random.randint(0, WIDTH - 2)
        y = random.randint(0, HEIGHT - 2)
        w = random.randint(1, 5)
        h = random.randint(1, 3)
        c = random.randint(120, 255)
        a = random.randint(40, 110)
        pygame.draw.rect(noise, (c, c, c, a), (x, y, w, h))
    surface.blit(noise, (0, 0))

    # Leggero flash rosso sporadico per tensione visiva.
    tint = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    tint.fill((30, 0, 0, random.randint(12, 38)))
    surface.blit(tint, (0, 0))

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if state == "menu":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    enter_game()
                elif event.key == pygame.K_ESCAPE:
                    running = False

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if play_button.collidepoint(event.pos):
                    enter_game()
                elif exit_button.collidepoint(event.pos):
                    audiomanager.play_sound(BUTTON_SOUND, volume=0.8)
                    running = False

        elif state == "night_intro":
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE):
                state = "game"
                orologio.start(pygame.time.get_ticks())

        elif state == "game":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    flashlight.toggle()
                elif event.key == pygame.K_m:
                    enter_menu(play_click=True)
                elif event.key == pygame.K_ESCAPE:
                    running = False

    if state == "menu":
        screen.blit(menu_background, (0, 0))

        dim = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 120))
        screen.blit(dim, (0, 0))

        title_jitter_x = random.randint(-2, 2)
        title_jitter_y = random.randint(-1, 1)
        title = font_title.render("Five Nights at School", True, (245, 245, 245))
        title_rect = title.get_rect(center=(WIDTH // 2 + title_jitter_x, HEIGHT // 3 - 30 + title_jitter_y))
        screen.blit(title, title_rect)

        draw_button(play_button, "Play")
        draw_button(exit_button, "Exit")
        draw_glitch_menu_overlay(screen)

    elif state == "night_intro":
        elapsed = pygame.time.get_ticks() - intro_start_time
        if elapsed >= INTRO_DURATION_MS:
            state = "game"

        screen.fill((0, 0, 0))

        title = font_night.render(f"Notte {current_night}", True, (235, 235, 235))
        hour = font_hour.render("Ore 12:00", True, (235, 235, 235))

        title_rect = title.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 40))
        hour_rect = hour.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 38))

        screen.blit(title, title_rect)
        screen.blit(hour, hour_rect)

    else:
        mouse_x, _ = pygame.mouse.get_pos()
        camera.update_from_cursor(mouse_x)
        cam_x = camera.get_offset_x()

        screen.blit(game_background, (-cam_x, 0))
        flashlight.draw(screen)
        label = orologio.update(pygame.time.get_ticks())
        clock_text = font_hour.render(label, True, (235, 235, 235))
        screen.blit(clock_text, clock_text.get_rect(topright=(WIDTH - 30, 24)))

        if orologio.is_finished():
            current_night += 1
            enter_menu()


    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()