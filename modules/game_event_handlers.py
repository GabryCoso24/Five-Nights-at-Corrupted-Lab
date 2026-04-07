import pygame

from modules.menu_settings_handlers import handle_menu_events as handle_menu_events_module
from modules.menu_settings_handlers import handle_settings_events as handle_settings_events_module


class GameEventHandlersMixin:
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F11:
                self.toggle_fullscreen()
                return
            if event.key == pygame.K_RETURN and (event.mod & pygame.KMOD_ALT):
                self.toggle_fullscreen()
                return

        if self.state == "menu":
            self.handle_menu_events(event)
        elif self.state == "settings":
            self.handle_settings_events(event)
        elif self.state == "night_intro":
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.start_gameplay()
        elif self.state == "night_tutorial":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_e:
                    self.start_gameplay()
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    current_page = int(getattr(self, "tutorial_page", 0) or 0)
                    if current_page < 1:
                        self.tutorial_page = current_page + 1
                    else:
                        self.start_gameplay()
        elif self.state == "night_outro":
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.enter_menu(play_click=True)
        elif self.state == "jumpscare":
            # Durante il jumpscare non permettere skip: a fine animazione parte il video.
            pass
        elif self.state == "defeat_video":
            if event.type == pygame.KEYDOWN and event.key == pygame.K_e:
                now_ms = pygame.time.get_ticks()
                # Evita skip immediato causato da tasti tenuti premuti (es. SPACE usato in game).
                if now_ms - self.defeat_video_started_at >= 700:
                    self.enter_menu(play_click=False)
        elif self.state == "victory_video":
            if event.type == pygame.KEYDOWN and event.key == pygame.K_e:
                now_ms = pygame.time.get_ticks()
                if now_ms - self.victory_video_started_at >= 700:
                    self.enter_menu(play_click=False)
        elif self.state == "endgame_video":
            if event.type == pygame.KEYDOWN and event.key == pygame.K_e:
                now_ms = pygame.time.get_ticks()
                if now_ms - self.endgame_video_started_at >= 700:
                    self._start_credits_video()
        elif self.state == "credits_video":
            if event.type == pygame.KEYDOWN and event.key == pygame.K_e:
                now_ms = pygame.time.get_ticks()
                if now_ms - self.credits_video_started_at >= 700:
                    self.enter_menu(play_click=False)
        elif self.state == "game":
            self.handle_game_events(event)

    def handle_menu_events(self, event):
        handle_menu_events_module(self, event)

    def handle_settings_events(self, event):
        handle_settings_events_module(self, event)

    def handle_game_events(self, event):
        handled, action = self.system_panel.handle_event(event, lock_open=self._is_any_rebooting())
        if handled:
            if action:
                self.handle_system_panel_action(action)
            return

        if self.video_camere.handle_event(event):
            self.blocked_vent_cameras = self.video_camere.get_blocked_vent_edges()
            if self.video_camere.is_open and self.flashlight_active:
                self.flashlight_active = False
                self.flashlight_repel_triggered = False
                self.flashlight_repelled_targets.clear()
            return

        if event.type != pygame.KEYDOWN:
            return

        if event.key == pygame.K_SPACE and self.flashlight_ready and not self.video_camere.is_open and not self.system_panel.is_open and not self.system_errors.get("flashlight", False):
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
