import pygame


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
        elif self.state == "night_intro":
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE):
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
