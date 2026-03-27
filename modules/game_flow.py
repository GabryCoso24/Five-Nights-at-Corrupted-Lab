import sys
import traceback

import pygame


class GameFlowMixin:
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
