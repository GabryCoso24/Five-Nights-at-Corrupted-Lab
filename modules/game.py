import random
import sys
import traceback
import os

import pygame

from modules.animatronics import build_default_manager
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
        self.can_continue = False
        self.error_message = None

        self.animatronics = build_default_manager()
        self.enemy_sprites = self._load_enemy_sprites()
        self.default_enemy_sprite = self.enemy_sprites.get("Chugginton")
        if self.default_enemy_sprite is None and self.enemy_sprites:
            self.default_enemy_sprite = next(iter(self.enemy_sprites.values()))

        self.jumpscare_name = ""
        self.jumpscare_start_time = 0
        self.jumpscare_duration_ms = 1900

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
        self.video_camere.set_threat_sprite(self.default_enemy_sprite)

        button_width, button_height = 280, 80
        center_x = (self.width - button_width) // 2
        self.new_game_button = pygame.Rect(center_x, self.height // 2 - 80, button_width, button_height)
        self.continue_button = pygame.Rect(center_x, self.height // 2 + 15, button_width, button_height)
        self.exit_button = pygame.Rect(center_x, self.height // 2 + 110, button_width, button_height)

        self.menu_music = "assets/audio/menu.wav"
        self.button_sound = "assets/audio/pulsanti.wav"
        self.intro_duration_ms = 2600
        self.outro_duration_ms = 2600
        self.music_fade_ms = 800

        self.audio.play_music(music_file=self.menu_music)

        self.intro_start_time = 0
        self.outro_start_time = 0

        self.flashlight_ready = True
        self.flashlight_active = False
        self.flashlight_activation_time = 0
        self.flashlight_duration_ms = 1300
        self.flashlight_cooldown_ms = 2500
        self.flashlight_cooldown_until = 0
        self.flashlight_repel_triggered = False
        self.flashlight_repelled_targets = set()
        self.flashlight_repel_feedback_until = 0
        self.flashlight_repel_sound = "assets/audio/switch_cam_sound.wav"

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
        elif self.state == "jumpscare":
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_ESCAPE):
                self.enter_menu(play_click=False)
        elif self.state == "game":
            self.handle_game_events(event)

    def handle_menu_events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                if self.can_continue:
                    self.continue_game()
                else:
                    self.start_new_game()
            elif event.key == pygame.K_ESCAPE:
                pygame.event.post(pygame.event.Event(pygame.QUIT))

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.new_game_button.collidepoint(event.pos):
                self.start_new_game()
            elif self.can_continue and self.continue_button.collidepoint(event.pos):
                self.continue_game()
            elif self.exit_button.collidepoint(event.pos):
                self.audio.play_sound(self.button_sound, volume=0.8)
                pygame.event.post(pygame.event.Event(pygame.QUIT))

    def handle_game_events(self, event):
        if self.video_camere.handle_event(event):
            return

        if event.type != pygame.KEYDOWN:
            return

        if event.key == pygame.K_SPACE and self.flashlight_ready:
            self.flashlight_active = True
            self.flashlight_activation_time = pygame.time.get_ticks()
            self.flashlight_ready = False
            self.flashlight_cooldown_until = self.flashlight_activation_time + self.flashlight_cooldown_ms
            self.flashlight_repel_triggered = False
            self.flashlight_repelled_targets.clear()
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
        elif self.state == "jumpscare":
            self.draw_jumpscare()
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

        self.queue_button(self.new_game_button, "New Game")
        if self.can_continue:
            self.queue_button(self.continue_button, "Continua")
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
            self.flashlight_repel_triggered = False
            self.flashlight_repelled_targets.clear()

        if self.flashlight_active:
            self.flashlight.draw(self.screen)
            # Repel any newly lit enemy while the beam stays active.
            lit_targets = self._get_flashlight_lit_targets(positions=self.animatronics.get_positions(), cam_x=cam_x)
            new_targets = [name for name in lit_targets if name not in self.flashlight_repelled_targets]
            repelled = self.animatronics.on_flashlight(now_ms, target_names=new_targets)
            if repelled:
                self.flashlight_repelled_targets.update(repelled)
                self.flashlight_repel_triggered = True
                self.flashlight_repel_feedback_until = now_ms + 360
                self.audio.play_sound(self.flashlight_repel_sound, volume=0.7)

        label = self.orologio.update(now_ms)

        watched_camera = self.video_camere.get_selected_camera_id() if self.video_camere.is_open else None
        player_can_defend = self.flashlight_ready or self.flashlight_active
        events = self.animatronics.update(
            now_ms=now_ms,
            night_level=self.current_night,
            watched_camera=watched_camera,
            player_can_defend=player_can_defend,
        )

        for event in events:
            if event.get("type") == "moved":
                self.video_camere.register_movement(
                    from_camera=event.get("from"),
                    to_camera=event.get("to"),
                    jam_duration_ms=2200,
                )
            if event.get("type") == "jumpscare":
                self.enter_jumpscare(event.get("name", "Sconosciuto"))
                return

        positions = self.animatronics.get_positions()
        threat_cameras = self.animatronics.get_cameras_with_presence()
        self.video_camere.set_threat_cameras(threat_cameras)

        if self.video_camere.is_open and watched_camera:
            threat_name = None
            for name, camera_id in positions.items():
                if camera_id == watched_camera:
                    threat_name = name
                    break
                if camera_id == "door_left" and watched_camera == "cam1":
                    threat_name = name
                    break
                if camera_id == "door_right" and watched_camera == "cam14":
                    threat_name = name
                    break
            self.video_camere.set_threat_sprite(self.enemy_sprites.get(threat_name, self.default_enemy_sprite))
        else:
            self.video_camere.set_threat_sprite(self.default_enemy_sprite)

        if not self.flashlight_ready and now_ms >= self.flashlight_cooldown_until:
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
            remaining_ms = max(0, self.flashlight_cooldown_until - now_ms)
            indicator_text = f"Flashlight: COOLDOWN {remaining_ms / 1000:.1f}s"
            indicator_color = (255, 80, 80)

        indicator_label = self.font_small.render(indicator_text, True, indicator_color)
        self.screen.blit(indicator_label, (24, 24))

        left_door_threats = [name for name, camera_id in positions.items() if camera_id == "door_left"]
        right_door_threats = [name for name, camera_id in positions.items() if camera_id == "door_right"]
        if left_door_threats:
            self._draw_door_threats(left_door_threats, cam_x, side="left")
        if right_door_threats:
            self._draw_door_threats(right_door_threats, cam_x, side="right")

        self.video_camere.update_hover(mouse_pos)
        self.video_camere.queue_trigger()
        draw_graphic_elements(self.screen)
        self.video_camere.draw_overlay(self.screen)

        if now_ms < self.flashlight_repel_feedback_until:
            self._draw_flashlight_repel_feedback(now_ms)

        if self.orologio.is_finished():
            self.current_night += 1
            self.can_continue = True
            self.exit_night()
            return

    def _enter_night_intro(self):
        self.audio.play_sound(self.button_sound, volume=0.8)
        self.audio.stop_music(fade_ms=self.music_fade_ms)
        self.intro_start_time = pygame.time.get_ticks()
        self.state = "night_intro"

    def start_new_game(self):
        self.current_night = 1
        self.can_continue = False
        self._enter_night_intro()

    def continue_game(self):
        if not self.can_continue:
            return
        self._enter_night_intro()

    def enter_game(self):
        # Backward-compatible alias.
        self.start_new_game()

    def start_gameplay(self):
        self.state = "game"
        self.orologio.start(pygame.time.get_ticks())
        self.flashlight_ready = True
        self.flashlight_active = False
        self.flashlight_repel_triggered = False
        self.flashlight_repelled_targets.clear()
        self.flashlight_cooldown_until = 0
        self.animatronics.reset()
        self.video_camere.set_threat_cameras([])
        self.jumpscare_name = ""
        self.video_camere.close()

    def enter_jumpscare(self, name):
        self.jumpscare_name = name
        self.jumpscare_start_time = pygame.time.get_ticks()
        self.state = "jumpscare"

    def draw_jumpscare(self):
        elapsed = pygame.time.get_ticks() - self.jumpscare_start_time
        if elapsed >= self.jumpscare_duration_ms:
            self.enter_menu(play_click=False)
            return

        self.screen.fill((0, 0, 0))
        sprite = self.enemy_sprites.get(self.jumpscare_name, self.default_enemy_sprite)
        if sprite is not None:
            target_h = int(self.height * 0.78)
            target_w = int(sprite.get_width() * (target_h / max(1, sprite.get_height())))
            target_w = min(target_w, int(self.width * 0.8))
            img = pygame.transform.smoothscale(sprite, (target_w, target_h)).convert_alpha()
            pulse = 205 + int(50 * abs((elapsed % 300) / 300 - 0.5))
            img.set_alpha(max(120, min(255, pulse)))
            self.screen.blit(img, img.get_rect(center=(self.width // 2, self.height // 2 + 20)))

        label = self.font_night.render("SEI STATO PRESO", True, (255, 80, 80))
        name_label = self.font_hour.render(self.jumpscare_name.upper(), True, (245, 245, 245))
        self.screen.blit(label, label.get_rect(center=(self.width // 2, 84)))
        self.screen.blit(name_label, name_label.get_rect(center=(self.width // 2, 152)))

    def _load_enemy_sprites(self):
        folder = os.path.join("assets", "images", "personaggi_cattivi")
        sprites = {}
        if not os.path.isdir(folder):
            return sprites

        valid_ext = {".png", ".jpg", ".jpeg", ".webp", ".jfif"}
        for filename in os.listdir(folder):
            ext = os.path.splitext(filename)[1].lower()
            if ext not in valid_ext:
                continue

            key = os.path.splitext(filename)[0].lower()
            if "chugginton" in key:
                name = "Chugginton"
            elif "linux" in key:
                name = "Linux"
            elif "luca" in key:
                name = "Luca"
            else:
                continue

            full_path = os.path.join(folder, filename)
            try:
                sprites[name] = pygame.image.load(full_path).convert_alpha()
            except Exception:
                try:
                    sprites[name] = pygame.image.load(full_path).convert()
                except Exception:
                    pass

        return sprites

    def _draw_door_threats(self, door_threats, cam_x, side="right"):
        # Anchor near the office side door in world space, then convert to screen space.
        if side == "left":
            door_world_x = int(self.game_background.get_width() * 0.24)
        else:
            door_world_x = self.game_background.get_width() - 320
        base_screen_x = door_world_x - cam_x
        base_screen_y = int(self.height * 0.26)

        for idx, name in enumerate(door_threats):
            sprite = self.enemy_sprites.get(name, self.default_enemy_sprite)
            if sprite is None:
                continue

            target_h = int(self.height * 0.38)
            target_w = int(sprite.get_width() * (target_h / max(1, sprite.get_height())))
            target_w = min(target_w, int(self.width * 0.34))
            img = pygame.transform.smoothscale(sprite, (target_w, target_h)).convert_alpha()
            img.set_alpha(228)

            x = base_screen_x + (idx * 56) - (target_w // 2)
            y = base_screen_y + (idx * 12)
            self.screen.blit(img, (x, y))

    def _get_flashlight_lit_targets(self, positions, cam_x):
        mouse_pos = pygame.mouse.get_pos()
        lit_targets = []

        left_door_threats = [name for name, camera_id in positions.items() if camera_id == "door_left"]
        right_door_threats = [name for name, camera_id in positions.items() if camera_id == "door_right"]

        for side, threats in (("left", left_door_threats), ("right", right_door_threats)):
            if side == "left":
                door_world_x = int(self.game_background.get_width() * 0.24)
            else:
                door_world_x = self.game_background.get_width() - 320
            base_screen_x = door_world_x - cam_x
            base_screen_y = int(self.height * 0.26)

            for idx, name in enumerate(threats):
                sprite = self.enemy_sprites.get(name, self.default_enemy_sprite)
                if sprite is None:
                    continue

                target_h = int(self.height * 0.38)
                target_w = int(sprite.get_width() * (target_h / max(1, sprite.get_height())))
                target_w = min(target_w, int(self.width * 0.34))
                x = base_screen_x + (idx * 56) - (target_w // 2)
                y = base_screen_y + (idx * 12)
                rect = pygame.Rect(x, y, target_w, target_h)

                if self._is_rect_hit_by_flashlight(rect, mouse_pos):
                    lit_targets.append(name)

        return lit_targets

    def _is_rect_hit_by_flashlight(self, rect, light_center):
        light_x, light_y = light_center
        closest_x = max(rect.left, min(light_x, rect.right))
        closest_y = max(rect.top, min(light_y, rect.bottom))
        dx = light_x - closest_x
        dy = light_y - closest_y
        return (dx * dx + dy * dy) <= (self.flashlight.radius * self.flashlight.radius)

    def _draw_flashlight_repel_feedback(self, now_ms):
        remaining = max(0, self.flashlight_repel_feedback_until - now_ms)
        alpha = int(165 * (remaining / 360.0))
        pulse = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        pulse.fill((210, 255, 235, max(0, min(180, alpha))))
        self.screen.blit(pulse, (0, 0))

        text = self.font_small.render("FLASH HIT", True, (230, 255, 240))
        text_shadow = self.font_small.render("FLASH HIT", True, (20, 30, 25))
        center = (self.width // 2, int(self.height * 0.18))
        self.screen.blit(text_shadow, text_shadow.get_rect(center=(center[0] + 2, center[1] + 2)))
        self.screen.blit(text, text.get_rect(center=center))

    def exit_night(self):
        self.audio.play_sound(self.button_sound, volume=0.8)
        self.audio.stop_music(fade_ms=self.music_fade_ms)
        self.outro_start_time = pygame.time.get_ticks()
        self.state = "night_outro"

    def enter_menu(self, play_click=False):
        if play_click:
            self.audio.play_sound(self.button_sound, volume=0.8)
        self.audio.play_music(music_file=self.menu_music, fade_ms=self.music_fade_ms)
        self.video_camere.set_threat_cameras([])
        self.video_camere.close()
        self.state = "menu"
