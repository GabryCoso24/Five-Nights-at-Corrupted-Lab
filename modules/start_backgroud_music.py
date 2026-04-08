"""Gestione audio centralizzata per musica, effetti sonori e loop ambientali."""

import pygame
from pathlib import Path

class AudioManager:
    """Avvolge pygame.mixer e mantiene cache di suoni, musica e canali attivi."""
    def __init__(self):
        """Inizializza il mixer se disponibile e prepara cache e canali audio."""
        self.enabled = True
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
        except pygame.error:
            # Continue without audio if mixer/audio device is not available.
            self.enabled = False
        self.current_music = None
        self.sounds = {}
        self.sound_channels = {}
        self.loop_channels = {}

    def play_music(self, music_file, loop=True, volume=0.5, fade_ms=0):
        """Avvia la musica di sottofondo e la riusa finché il file non cambia."""
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
        """Ferma la musica corrente, con dissolvenza se richiesto."""
        if not self.enabled:
            return
        if fade_ms > 0:
            pygame.mixer.music.fadeout(fade_ms)
        else:
            pygame.mixer.music.stop()
        self.current_music = None

    def set_music_volume(self, volume):
        """Imposta il volume della musica mantenendolo tra 0 e 1."""
        if not self.enabled:
            return
        clamped = max(0.0, min(1.0, float(volume)))
        pygame.mixer.music.set_volume(clamped)

    def pause_music(self):
        """Mettere in pausa la musica corrente."""
        if not self.enabled:
            return
        pygame.mixer.music.pause()

    def resume_music(self):
        """Riprende la musica precedentemente messa in pausa."""
        if not self.enabled:
            return
        pygame.mixer.music.unpause()

    def play_sound(self, sound_file, volume=1):
        """Carica se necessario e riproduce un effetto sonoro una volta sola."""
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
        channel = sound.play()
        if channel is None:
            return False
        self.sound_channels[sound_file] = channel
        return True

    def stop_sound(self, sound_file):
        """Ferma il canale associato a un effetto sonoro specifico."""
        if not self.enabled:
            return
        channel = self.sound_channels.pop(sound_file, None)
        if channel is not None:
            channel.stop()

    def is_sound_playing(self, sound_file):
        """Verifica se l'effetto sonoro richiesto è ancora in riproduzione."""
        if not self.enabled:
            return False
        channel = self.sound_channels.get(sound_file)
        if channel is None:
            return False
        return bool(channel.get_busy())

    def start_loop_sound(self, sound_file, volume=1):
        """Avvia un suono in loop continuo, riusando il canale se è già attivo."""
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
        """Ferma il loop sonoro indicato se è in esecuzione."""
        if not self.enabled:
            return
        channel = self.loop_channels.pop(sound_file, None)
        if channel is not None:
            channel.stop()

