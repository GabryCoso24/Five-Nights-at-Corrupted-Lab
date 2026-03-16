import random
import sys
import traceback

import pygame

from modules.camera import Camera
from modules.cameras_system import VideoCamere
from modules.flashlight import Flashlight
from modules.orario import Orario
from modules.startBackgroudMusic import AudioManager
from modules.ui_manager import add_graphic_element, draw_graphic_elements


class Game:
    def __init__(self, width, height):
        self.width = width
        self.height = height

        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Five Nights at The Corrupted Lab")
        self.clock = pygame.time.Clock()

        self.state = "menu"
        self.current_night = 1
        self.error_message = None

        self.orologio = Orario()

        base_background = pygame.image.load("assets/images/ufficio.webp").convert()
        self.menu_background = pygame.transform.scale(base_background, (self.width, self.height))
        self.game_background = pygame.transform.scale(base_background, (int(self.width * 1.7), self.height))

        self.flashlight = Flashlight(self.width, self.height, radius=120, alpha=200)
        self.camera = Camera(self.width, self.game_background.get_width(), smoothing=0.13)
        self.audio = AudioManager()

        self.font_title = pygame.font.SysFont(None, 96)
        self.font_button = pygame.font.SysFont(None, 56)
        self.font_night = pygame.font.SysFont(None, 92)
        self.font_hour = pygame.font.SysFont(None, 68)
        self.font_small = pygame.font.SysFont(None, 36)

        self.video_camere = VideoCamere(
            width=self.width,
            height=self.height,
            label_font=self.font_small,
            title_font=self.font_hour,
        )

        self.video_camere.set_trigger_rect(
            x=self.width - 70,
            y=self.height/2 - 250,
            w=100,
            h=250
        )

        button_width, button_height = 280, 80
        self.play_button = pygame.Rect((self.width - button_width) // 2, self.height // 2 - 20, button_width, button_height)
        self.exit_button = pygame.Rect((self.width - button_width) // 2, self.height // 2 + 90, button_width, button_height)

        self.menu_music = "assets/audio/menu.wav"
        self.button_sound = "assets/audio/pulsanti.wav"
        self.intro_duration_ms = 2600
        self.outro_duration_ms = 2600
        self.music_fade_ms = 800

        self.audio.play_music(music_file=self.menu_music)

        self.intro_start_time = 0
        self.outro_start_time = 0

        self.flashlight_ready = True
        self.flashlight_last_used_hour = -1
        self.flashlight_active = False
        self.flashlight_activation_time = 0
        self.flashlight_duration_ms = 2000
        self.flashlight_cooldown_hours = 2

    def run(self):
        running = True
        while running:
            try:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                        continue
                    self.handle_event(event)

                self.update_and_draw()
                pygame.display.flip()
                self.clock.tick(60)
                self.error_message = None
            except Exception as exc:
                self.error_message = f"Errore: {exc}"
                traceback.print_exc()

        pygame.quit()
        sys.exit()

    def handle_event(self, event):
        if self.state == "menu":
            self.handle_menu_events(event)
        elif self.state == "night_intro":
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.start_gameplay()
        elif self.state == "night_outro":
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.enter_menu(play_click=True)
        elif self.state == "game":
            self.handle_game_events(event)

    def handle_menu_events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self.enter_game()
            elif event.key == pygame.K_ESCAPE:
                pygame.event.post(pygame.event.Event(pygame.QUIT))

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.play_button.collidepoint(event.pos):
                self.enter_game()
            elif self.exit_button.collidepoint(event.pos):
                self.audio.play_sound(self.button_sound, volume=0.8)
                pygame.event.post(pygame.event.Event(pygame.QUIT))

    def handle_game_events(self, event):
        if event.type != pygame.KEYDOWN:
            return

        if event.key == pygame.K_SPACE and self.flashlight_ready:
            self.flashlight_active = True
            self.flashlight_activation_time = pygame.time.get_ticks()
            self.flashlight_ready = False
            self.flashlight_last_used_hour = self.orologio.hour_index
        elif event.key == pygame.K_m:
            self.enter_menu(play_click=True)
        elif event.key == pygame.K_ESCAPE:
            pygame.event.post(pygame.event.Event(pygame.QUIT))

    def update_and_draw(self):
        if self.state == "menu":
            self.draw_menu()
        elif self.state == "night_intro":
            self.draw_night_intro()
        elif self.state == "night_outro":
            self.draw_night_outro()
        elif self.state == "game":
            self.draw_game()

    def draw_menu(self):
        self.screen.blit(self.menu_background, (0, 0))

        dim = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 120))
        self.screen.blit(dim, (0, 0))

        title_jitter_x = random.randint(-2, 2)
        title_jitter_y = random.randint(-1, 1)
        title = self.font_title.render("Five Nights at The Corrupted Lab", True, (245, 245, 245))
        title_rect = title.get_rect(center=(self.width // 2 + title_jitter_x, self.height // 3 - 30 + title_jitter_y))
        self.screen.blit(title, title_rect)

        self.queue_button(self.play_button, "Play")
        self.queue_button(self.exit_button, "Exit")
        draw_graphic_elements(self.screen)

        self.draw_glitch_overlay(self.screen)

        if self.error_message:
            err_label = self.font_small.render(self.error_message, True, (255, 60, 60))
            err_rect = err_label.get_rect(center=(self.width // 2, self.height - 60))
            self.screen.blit(err_label, err_rect)

    def queue_button(self, rect, text):
        hovered = rect.collidepoint(pygame.mouse.get_pos())
        color = (210, 210, 210) if hovered else (170, 170, 170)
        add_graphic_element(
            rect=rect,
            text=text,
            color=color,
            font=self.font_button,
            text_color=(25, 25, 25),
            border_radius=14,
            border_color=(40, 40, 40),
            border_width=3,
        )

    def draw_glitch_overlay(self, surface):
        scanlines = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        for y in range(0, self.height, 4):
            pygame.draw.line(scanlines, (0, 0, 0, 24), (0, y), (self.width, y))
        surface.blit(scanlines, (0, 0))

        if random.random() > 0.16:
            return

        snapshot = surface.copy()

        for _ in range(random.randint(6, 16)):
            y = random.randint(0, self.height - 6)
            h = random.randint(2, 10)
            shift = random.randint(-45, 45)
            src = pygame.Rect(0, y, self.width, h)
            surface.blit(snapshot, (shift, y), src)

        noise = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        for _ in range(240):
            x = random.randint(0, self.width - 2)
            y = random.randint(0, self.height - 2)
            w = random.randint(1, 5)
            h = random.randint(1, 3)
            c = random.randint(120, 255)
            a = random.randint(40, 110)
            pygame.draw.rect(noise, (c, c, c, a), (x, y, w, h))
        surface.blit(noise, (0, 0))

        tint = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        tint.fill((30, 0, 0, random.randint(12, 38)))
        surface.blit(tint, (0, 0))

    def draw_night_intro(self):
        elapsed = pygame.time.get_ticks() - self.intro_start_time
        if elapsed >= self.intro_duration_ms:
            self.start_gameplay()

        self.screen.fill((0, 0, 0))
        title = self.font_night.render(f"Notte {self.current_night}", True, (235, 235, 235))
        hour = self.font_hour.render("Ore 12:00", True, (235, 235, 235))
        self.screen.blit(title, title.get_rect(center=(self.width // 2, self.height // 2 - 40)))
        self.screen.blit(hour, hour.get_rect(center=(self.width // 2, self.height // 2 + 38)))

    def draw_night_outro(self):
        elapsed = pygame.time.get_ticks() - self.outro_start_time
        if elapsed >= self.outro_duration_ms:
            self.enter_menu(play_click=True)

        self.screen.fill((0, 0, 0))
        title = self.font_night.render(f"Notte {self.current_night - 1}", True, (235, 235, 235))
        desc = self.font_night.render("SUPERATA!!", True, (235, 235, 235))
        self.screen.blit(title, title.get_rect(center=(self.width // 2, self.height // 2 - 40)))
        self.screen.blit(desc, desc.get_rect(center=(self.width // 2, self.height // 2 + 38)))

    def draw_game(self):
        mouse_pos = pygame.mouse.get_pos()
        mouse_x, _ = mouse_pos
        self.camera.update_from_cursor(mouse_x)
        cam_x = self.camera.get_offset_x()

        self.screen.blit(self.game_background, (-cam_x, 0))

        now_ms = pygame.time.get_ticks()
        if self.flashlight_active and now_ms - self.flashlight_activation_time >= self.flashlight_duration_ms:
            self.flashlight_active = False

        if self.flashlight_active:
            self.flashlight.draw(self.screen)

        label = self.orologio.update(now_ms)

        if not self.flashlight_ready:
            if self.orologio.hour_index - self.flashlight_last_used_hour >= self.flashlight_cooldown_hours:
                self.flashlight_ready = True

        clock_text = self.font_hour.render(label, True, (235, 235, 235))
        self.screen.blit(clock_text, clock_text.get_rect(topright=(self.width - 30, 24)))

        if self.flashlight_active:
            indicator_text = "Flashlight: ATTIVA"
            indicator_color = (80, 255, 80)
        elif self.flashlight_ready:
            indicator_text = "Flashlight: PRONTA"
            indicator_color = (80, 80, 255)
        else:
            indicator_text = "Flashlight: COOLDOWN"
            indicator_color = (255, 80, 80)

        indicator_label = self.font_small.render(indicator_text, True, indicator_color)
        self.screen.blit(indicator_label, (24, 24))

        self.video_camere.update_hover(mouse_pos)
        self.video_camere.queue_trigger()
        draw_graphic_elements(self.screen)
        self.video_camere.draw_overlay(self.screen)

        if self.orologio.is_finished():
            self.current_night += 1
            self.exit_night()

    def enter_game(self):
        self.audio.play_sound(self.button_sound, volume=0.8)
        self.audio.stop_music(fade_ms=self.music_fade_ms)
        self.intro_start_time = pygame.time.get_ticks()
        self.state = "night_intro"

    def start_gameplay(self):
        self.state = "game"
        self.orologio.start(pygame.time.get_ticks())
        self.flashlight_ready = True
        self.flashlight_active = False
        self.flashlight_last_used_hour = -1

    def exit_night(self):
        self.audio.play_sound(self.button_sound, volume=0.8)
        self.audio.stop_music(fade_ms=self.music_fade_ms)
        self.outro_start_time = pygame.time.get_ticks()
        self.state = "night_outro"

    def enter_menu(self, play_click=False):
        if play_click:
            self.audio.play_sound(self.button_sound, volume=0.8)
        self.audio.play_music(music_file=self.menu_music, fade_ms=self.music_fade_ms)
        self.state = "menu"
