import pygame
from pathlib import Path

class AudioManager:
    def __init__(self):
        self.enabled = True
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
        except pygame.error:
            # Continue without audio if mixer/audio device is not available.
            self.enabled = False
        self.current_music = None
        self.sounds = {}
        self.loop_channels = {}

    def play_music(self, music_file, loop=True, volume=0.5, fade_ms=0):
        if not self.enabled:
            return False
        if not Path(music_file).exists():
            return False

        if self.current_music != music_file:
            try:
                pygame.mixer.music.load(music_file)
                pygame.mixer.music.set_volume(volume)
                pygame.mixer.music.play(-1 if loop else 0, fade_ms=fade_ms)
            except pygame.error:
                return False
            self.current_music = music_file
        return True

    def stop_music(self, fade_ms=0):
        if not self.enabled:
            return
        if fade_ms > 0:
            pygame.mixer.music.fadeout(fade_ms)
        else:
            pygame.mixer.music.stop()
        self.current_music = None

    def set_music_volume(self, volume):
        if not self.enabled:
            return
        clamped = max(0.0, min(1.0, float(volume)))
        pygame.mixer.music.set_volume(clamped)

    def pause_music(self):
        if not self.enabled:
            return
        pygame.mixer.music.pause()

    def resume_music(self):
        if not self.enabled:
            return
        pygame.mixer.music.unpause()

    def play_sound(self, sound_file, volume=1):
        if not self.enabled:
            return False
        if not Path(sound_file).exists():
            return False

        if sound_file not in self.sounds:
            try:
                self.sounds[sound_file] = pygame.mixer.Sound(sound_file)
            except pygame.error:
                return False

        sound = self.sounds[sound_file]
        sound.set_volume(volume)
        sound.play()
        return True

    def start_loop_sound(self, sound_file, volume=1):
        if not self.enabled:
            return False
        if not Path(sound_file).exists():
            return False

        if sound_file not in self.sounds:
            try:
                self.sounds[sound_file] = pygame.mixer.Sound(sound_file)
            except pygame.error:
                return False

        existing = self.loop_channels.get(sound_file)
        if existing is not None and existing.get_busy():
            existing.set_volume(volume)
            return True

        sound = self.sounds[sound_file]
        sound.set_volume(volume)
        channel = sound.play(loops=-1)
        if channel is None:
            return False
        self.loop_channels[sound_file] = channel
        return True

    def stop_loop_sound(self, sound_file):
        if not self.enabled:
            return
        channel = self.loop_channels.pop(sound_file, None)
        if channel is not None:
            channel.stop()