import sys
import traceback
import os

import pygame

try:
    import cv2
except Exception:
    cv2 = None


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
        elif self.state == "defeat_video":
            self.draw_defeat_video()
        elif self.state == "victory_video":
            self.draw_victory_video()
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
        self._stop_defeat_video()
        self._stop_victory_video()
        self.video_camere.close()

    def enter_jumpscare(self, name):
        self.jumpscare_name = name
        self.jumpscare_start_time = pygame.time.get_ticks()
        self.state = "jumpscare"

    def _start_defeat_video(self):
        self._stop_defeat_video()
        self.defeat_video_started_at = pygame.time.get_ticks()
        self.defeat_video_last_frame_at = 0
        self.defeat_video_path = None
        self.defeat_video_audio_started = False

        for candidate in getattr(self, "defeat_video_candidates", []):
            if os.path.isfile(candidate):
                self.defeat_video_path = candidate
                break

        if self.defeat_video_path and cv2 is not None:
            try:
                self.defeat_video_cap = cv2.VideoCapture(self.defeat_video_path)
                if not self.defeat_video_cap.isOpened():
                    self.defeat_video_cap = None
            except Exception:
                self.defeat_video_cap = None

        # Prova prima a usare direttamente il file video come sorgente audio.
        if self.defeat_video_path:
            self.defeat_video_audio_started = self.audio.play_music(
                music_file=self.defeat_video_path,
                loop=False,
                volume=1.0,
            )

        # Fallback: usa un file audio dedicato con stesso contenuto del video.
        if not self.defeat_video_audio_started:
            for candidate in getattr(self, "defeat_video_audio_candidates", []):
                if not os.path.isfile(candidate):
                    continue
                self.defeat_video_audio_started = self.audio.play_music(
                    music_file=candidate,
                    loop=False,
                    volume=1.0,
                )
                if self.defeat_video_audio_started:
                    break

        self.state = "defeat_video"

    def _stop_defeat_video(self):
        if self.defeat_video_cap is not None:
            try:
                self.defeat_video_cap.release()
            except Exception:
                pass
        if self.defeat_video_audio_started:
            self.audio.stop_music()
        self.defeat_video_cap = None
        self.defeat_video_path = None
        self.defeat_video_audio_started = False

    def _start_victory_video(self):
        self._stop_victory_video()
        self.victory_video_started_at = pygame.time.get_ticks()
        self.victory_video_last_frame_at = 0
        self.victory_video_path = None
        self.victory_video_audio_started = False

        for candidate in getattr(self, "victory_video_candidates", []):
            if os.path.isfile(candidate):
                self.victory_video_path = candidate
                break

        if self.victory_video_path and cv2 is not None:
            try:
                self.victory_video_cap = cv2.VideoCapture(self.victory_video_path)
                if not self.victory_video_cap.isOpened():
                    self.victory_video_cap = None
            except Exception:
                self.victory_video_cap = None

        if self.victory_video_path:
            self.victory_video_audio_started = self.audio.play_music(
                music_file=self.victory_video_path,
                loop=False,
                volume=1.0,
            )

        if not self.victory_video_audio_started:
            for candidate in getattr(self, "victory_video_audio_candidates", []):
                if not os.path.isfile(candidate):
                    continue
                self.victory_video_audio_started = self.audio.play_music(
                    music_file=candidate,
                    loop=False,
                    volume=1.0,
                )
                if self.victory_video_audio_started:
                    break

        self.state = "victory_video"

    def _stop_victory_video(self):
        if self.victory_video_cap is not None:
            try:
                self.victory_video_cap.release()
            except Exception:
                pass
        if self.victory_video_audio_started:
            self.audio.stop_music()
        self.victory_video_cap = None
        self.victory_video_path = None
        self.victory_video_audio_started = False

    def exit_night(self):
        self.audio.play_sound(self.button_sound, volume=0.8)
        self.audio.stop_music(fade_ms=self.music_fade_ms)
        self._start_victory_video()

    def enter_menu(self, play_click=False):
        if play_click:
            self.audio.play_sound(self.button_sound, volume=0.8)
        self._stop_defeat_video()
        self._stop_victory_video()
        self.audio.play_music(music_file=self.menu_music, fade_ms=self.music_fade_ms)
        self.video_camere.set_threat_cameras([])
        self.video_camere.close()
        self.state = "menu"
