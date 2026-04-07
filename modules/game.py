import os
import json

import pygame

from modules.animatronics import build_default_manager
from modules.camera import Camera
from modules.cameras_system import VideoCamere
from modules.flashlight import Flashlight
from modules.game_assets import load_enemy_sprites, load_jumpscare_assets
from modules.game_event_handlers import GameEventHandlersMixin
from modules.game_flow import GameFlowMixin
from modules.game_rendering import GameRenderingMixin
from modules.hours import Orario
from modules.start_backgroud_music import AudioManager
from modules.system_panel import SystemPanel


class Game(GameFlowMixin, GameEventHandlersMixin, GameRenderingMixin):
    TRANSLATIONS = {
        "en": {
            "menu.new_game": "New Game",
            "menu.continue": "Continue",
            "menu.credits": "Credits",
            "menu.settings": "Settings",
            "menu.exit": "Exit",
            "settings.title": "Settings",
            "settings.display_mode": "Display mode",
            "settings.window_size": "Window size",
            "settings.cursor_size": "Cursor size:",
            "settings.language": "Language",
            "settings.back": "Back",
            "settings.mode.windowed": "Windowed",
            "settings.mode.windowed_borderless": "Borderless",
            "settings.mode.fullscreen": "Fullscreen",
            "settings.language.en": "English",
            "settings.language.it": "Italian",
            "loading.default": "Loading",
            "loading.night": "Loading Night {night}",
            "loading.resume": "Restoring Night {night}",
            "loading.prepare": "Preparing systems",
            "ui.night": "Night {night}",
            "ui.hour_start": "12:00 AM",
            "ui.night_cleared": "CLEARED!!",
            "ui.victory": "NIGHT CLEARED",
            "ui.video_unavailable": "Video unavailable",
            "ui.victory_video_unavailable": "Victory video unavailable",
            "ui.endgame_video_unavailable": "Endgame video unavailable",
            "ui.press_e_skip": "Press E to skip",
            "ui.flashlight_error": "Flashlight: ERROR",
            "ui.flashlight_active": "Flashlight: ACTIVE",
            "ui.flashlight_ready": "Flashlight: READY",
            "ui.flashlight_cooldown": "Flashlight: COOLDOWN {seconds:.1f}s",
            "ui.mute_call": "mute call",
            "ui.system_trigger": "SYSTEM",
            "ui.system_title": "system restart",
            "ui.system_menu": "menu>>>",
            "ui.system_camera": "camera system",
            "ui.system_ventilation": "ventilation",
            "ui.system_flashlight": "flashlight",
            "ui.system_reboot_camera": "reboot camera",
            "ui.system_reboot_ventilation": "reboot ventilation",
            "ui.system_reboot_flashlight": "reboot flashlight",
            "ui.system_reboot_all": "reboot all",
            "ui.system_exit": "exit",
            "ui.system_reboot_remaining": "reboot {seconds:.1f}s",
            "ui.system_error": "error",
            "ui.system_ok": "ok",
            "ui.cam_trigger": "CAM",
            "ui.cam_system_title": "CAMERAS SYSTEM",
            "ui.cam_no_feeds": "No camera images found in assets/images/cams",
            "ui.cam_error": "CAM ERROR",
            "ui.cam_movement": "MOVEMENT DETECTED",
            "ui.cam_map_main": "Map\nMain",
            "ui.cam_map_vents": "Map\nVents",
            "ui.cam_label": "CAM",
            "ui.cam_office_left": "OFFICE LEFT",
            "ui.cam_office_right": "OFFICE RIGHT",
            "ui.cam_admin_hint": "ADMIN: drag=move | double-click line=add node | drag node=shape path | vent: double-click close/open (1 only) | drag+wheel, shift+wheel=H | right-click line=remove | right-click cam/node/vent-rect=toggle link | middle=triangle | S=save",
            "tutorial.skip": "Press E to skip tutorial",
            "credits.thanks": "Thanks for playing",
        },
        "it": {
            "menu.new_game": "Nuova partita",
            "menu.continue": "Continua",
            "menu.credits": "Crediti",
            "menu.settings": "Impostazioni",
            "menu.exit": "Esci",
            "settings.title": "Impostazioni",
            "settings.display_mode": "Modalita schermo",
            "settings.window_size": "Dimensione finestra",
            "settings.cursor_size": "Dimensione cursore:",
            "settings.language": "Lingua",
            "settings.back": "Indietro",
            "settings.mode.windowed": "Finestra",
            "settings.mode.windowed_borderless": "Senza bordi",
            "settings.mode.fullscreen": "Schermo intero",
            "settings.language.en": "Inglese",
            "settings.language.it": "Italiano",
            "loading.default": "Caricamento",
            "loading.night": "Caricamento Notte {night}",
            "loading.resume": "Ripristino Notte {night}",
            "loading.prepare": "Preparazione sistemi",
            "ui.night": "Notte {night}",
            "ui.hour_start": "Ore 12:00",
            "ui.night_cleared": "SUPERATA!!",
            "ui.victory": "NOTTE SUPERATA",
            "ui.video_unavailable": "Video non disponibile",
            "ui.victory_video_unavailable": "Video vittoria non disponibile",
            "ui.endgame_video_unavailable": "Video endgame non disponibile",
            "ui.press_e_skip": "Premi E per saltare",
            "ui.flashlight_error": "Torcia: ERRORE",
            "ui.flashlight_active": "Torcia: ATTIVA",
            "ui.flashlight_ready": "Torcia: PRONTA",
            "ui.flashlight_cooldown": "Torcia: RICARICA {seconds:.1f}s",
            "ui.mute_call": "mute call",
            "ui.system_trigger": "SISTEMA",
            "ui.system_title": "riavvio sistema",
            "ui.system_menu": "menu>>>",
            "ui.system_camera": "sistema telecamere",
            "ui.system_ventilation": "ventilazione",
            "ui.system_flashlight": "torcia",
            "ui.system_reboot_camera": "riavvia telecamere",
            "ui.system_reboot_ventilation": "riavvia ventilazione",
            "ui.system_reboot_flashlight": "riavvia torcia",
            "ui.system_reboot_all": "riavvia tutto",
            "ui.system_exit": "esci",
            "ui.system_reboot_remaining": "riavvio {seconds:.1f}s",
            "ui.system_error": "errore",
            "ui.system_ok": "ok",
            "ui.cam_trigger": "CAM",
            "ui.cam_system_title": "SISTEMA CAMERE",
            "ui.cam_no_feeds": "Nessuna immagine camera trovata in assets/images/cams",
            "ui.cam_error": "ERRORE CAM",
            "ui.cam_movement": "MOVIMENTO RILEVATO",
            "ui.cam_map_main": "Mappa\nPrincipale",
            "ui.cam_map_vents": "Mappa\nCondotti",
            "ui.cam_label": "CAM",
            "ui.cam_office_left": "UFFICIO SINISTRA",
            "ui.cam_office_right": "UFFICIO DESTRA",
            "ui.cam_admin_hint": "ADMIN: drag=sposta | doppio click linea=aggiungi nodo | drag nodo=modifica percorso | condotti: doppio click chiude/apre (solo 1) | drag+ruota, shift+ruota=H | tasto destro linea=rimuovi | tasto destro cam/nodo/rettangolo=toggle link | centrale=triangolo | S=salva",
            "tutorial.skip": "Premi E per saltare il tutorial",
            "credits.thanks": "Grazie per aver giocato",
        },
    }

    def __init__(self, width, height):
        self.width = int(width)
        self.height = int(height)
        self.max_night = 5
        self.progress_save_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "savegame.json",
        )
        self.settings_save_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "settings.json",
        )

        self.display_mode = "windowed_borderless"
        self.display_mode_options = ["windowed", "windowed_borderless", "fullscreen"]
        self.window_size_options = [(1280, 720), (1600, 900), (1920, 1080)]
        if (self.width, self.height) not in self.window_size_options:
            self.window_size_options.append((self.width, self.height))
        self.window_size_options = sorted(set(self.window_size_options), key=lambda s: (s[0] * s[1], s[0]))
        self.window_size = (1920, 1080)

        self.cursor_size_options = [32, 48, 64]
        self.selected_cursor_size = 32
        self.cursor_fallback_path = os.path.join("assets", "images", "cursor.png")
        self.language_options = ["en", "it"]
        self.language = "en"

        self._load_settings()

        self.screen = None
        self._apply_display_mode()
        pygame.display.set_caption("Five Nights at The Corrupted Lab")
        self.clock = pygame.time.Clock()

        self.state = "menu"
        self.loading_message = self.tr("loading.default")
        self.loading_started_at = 0
        self.loading_duration_ms = 850
        self.loading_next_action = None
        self.current_night = 1
        self.last_completed_night = 0
        self.can_continue = False
        self.error_message = None

        self.animatronics = build_default_manager()
        self.enemy_sprites = load_enemy_sprites()
        self.jumpscare_assets = load_jumpscare_assets()
        self.default_enemy_sprite = self.enemy_sprites.get("Chugginton")
        if self.default_enemy_sprite is None and self.enemy_sprites:
            self.default_enemy_sprite = next(iter(self.enemy_sprites.values()))

        self.jumpscare_name = ""
        self.jumpscare_start_time = 0
        self.jumpscare_duration_ms = 1900
        self.jumpscare_video_path = None
        self.jumpscare_audio_path = None
        self.jumpscare_frames = []
        self.jumpscare_video_cap = None
        self.jumpscare_audio_started = False
        self.jumpscare_last_frame_at = 0
        self.jumpscare_frame_delay_ms = 33
        self.jumpscare_last_surface = None
        self.jumpscare_flash_duration_ms = 230
        self.jumpscare_shake_duration_ms = 900
        self.jumpscare_shake_strength = 34
        self.jumpscare_continue_game = False
        self.jumpscare_pending_error = None

        self.orologio = Orario()

        self.base_background = pygame.image.load("assets/images/ufficio.webp").convert()
        self.menu_background = pygame.transform.scale(self.base_background, (self.width, self.height))
        self.game_background = pygame.transform.scale(self.base_background, (int(self.width * 1.7), self.height))

        self.flashlight = Flashlight(self.width, self.height, radius=120, alpha=200)
        self.camera = Camera(self.width, self.game_background.get_width(), smoothing=0.13)
        self.audio = AudioManager()
        self.custom_cursor_path = self._get_cursor_path_for_size(self.selected_cursor_size)
        self.custom_cursor_hotspot = (0, 0)
        self.custom_cursor_surface = None
        if not self._load_custom_cursor():
            self.custom_cursor_path = self.cursor_fallback_path
            self._load_custom_cursor()

        def _pick_font(candidates):
            for name in candidates:
                try:
                    if pygame.font.match_font(name):
                        return name
                except Exception:
                    continue
            return None

        title_font_name = _pick_font(["bahnschrift", "impact", "arial black", "verdana"])
        ui_font_name = _pick_font(["trebuchet ms", "segoe ui", "verdana", "arial"])

        self.font_title = pygame.font.SysFont(title_font_name, 102, bold=True)
        self.font_button = pygame.font.SysFont(ui_font_name, 52, bold=True)
        self.font_night = pygame.font.SysFont(title_font_name, 92, bold=True)
        self.font_hour = pygame.font.SysFont(ui_font_name, 68, bold=True)
        self.font_small = pygame.font.SysFont(ui_font_name, 34)

        self.credits_roll_script = self._build_credits_script(self.language)

        self.video_camere = VideoCamere(
            width=self.width,
            height=self.height,
            label_font=self.font_small,
            title_font=self.font_hour,
        )

        self.video_camere.set_trigger_rect(
            x=self.width - 92,
            y=self.height / 2 - 255,
            w=82,
            h=210
        )
        self.video_camere.set_threat_sprite(self.default_enemy_sprite)

        self.system_panel = SystemPanel(
            width=self.width,
            height=self.height,
            label_font=self.font_small,
            title_font=self.font_hour,
        )
        self.system_panel.set_trigger_rect(
            x=18,
            y=self.height - 94,
            w=210,
            h=82,
        )
        self.system_errors = {
            "camera": False,
            "ventilation": False,
            "flashlight": False,
        }
        self.system_reboot_duration_ms = 5000
        self.system_reboots = {
            "camera": 0,
            "ventilation": 0,
            "flashlight": 0,
        }
        self.random_system_errors_enabled = True
        self.random_error_min_interval_ms = 26000
        self.random_error_max_interval_ms = 46000
        self.random_error_trigger_chance = 0.58
        self.random_error_multi_weights = {
            1: 0.84,
            2: 0.13,
            3: 0.03,
        }
        self.next_random_system_error_at = 0
        self.blocked_vent_cameras = set()

        self.error_animatronic_visibility_delay_ms = 45000

        self.new_game_button = pygame.Rect(0, 0, 0, 0)
        self.continue_button = pygame.Rect(0, 0, 0, 0)
        self.credits_button = pygame.Rect(0, 0, 0, 0)
        self.settings_button = pygame.Rect(0, 0, 0, 0)
        self.exit_button = pygame.Rect(0, 0, 0, 0)
        self.settings_back_button = pygame.Rect(0, 0, 0, 0)
        self.settings_display_mode_buttons = {}
        self.settings_window_size_buttons = {}
        self.settings_cursor_size_buttons = {}
        self.settings_language_buttons = {}

        self.menu_music = "assets/audio/menu.wav"
        self.night_start_sound = "assets/audio/night_start.wav"
        self.gameplay_ambience_music = "assets/audio/ambience.wav"
        self.button_sound = "assets/audio/pulsanti.wav"
        self.intro_duration_ms = 2600
        self.outro_duration_ms = 2600
        self.music_fade_ms = 800
        self.gameplay_ambience_volume = 0.42

        self.audio.play_music(music_file=self.menu_music)

        self.intro_start_time = 0
        self.outro_start_time = 0
        self.tutorial_started_at = 0
        self.tutorial_page = 0
        self.first_night_tutorial_seen = False

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
        self.flashlight_hit_sound = "assets/audio/control-shock.wav"
        self.current_night_call_path = None
        self.current_night_call_muted = False
        self.call_mute_button_rect = pygame.Rect(0, 0, 0, 0)
        self.system_error_sound = "assets/audio/error.wav"
        self.vent_enter_sound = "assets/audio/vents.wav"
        self.system_reboot_sound = "assets/audio/reboot.wav"
        self.office_entry_sounds = {
            "McQeen": "assets/audio/mqueen_in_office.wav",
            "Chugginton" : "assets/audio/chugginton_in_office.wav"
        }
        self.office_entry_sound_volume = 0.62
        self._office_entry_sound_cooldown_ms = 1000
        self._last_office_entry_sound_at = {}
        self._last_vent_enter_sound_at = 0
        self._vent_enter_sound_cooldown_ms = 500
        self._last_system_error_sound_at = 0
        self._system_error_sound_cooldown_ms = 450
        self._last_reboot_sound_at = 0
        self._reboot_sound_cooldown_ms = 300
        self._vent_move_sound_until = 0
        self.defeat_video_candidates = [
            os.path.join("assets", "video", "querelato.mp4"),
            "querelato.mp4",
        ]
        self.defeat_video_audio_candidates = [
            os.path.join("assets", "audio", "querelato.wav"),
            os.path.join("assets", "audio", "querelato.mp3"),
            os.path.join("assets", "audio", "querelato.ogg"),
            "querelato.wav",
            "querelato.mp3",
            "querelato.ogg",
        ]
        self.defeat_video_path = None
        self.defeat_video_cap = None
        self.defeat_video_audio_started = False
        self.defeat_video_started_at = 0
        self.defeat_video_last_frame_at = 0
        self.defeat_video_frame_delay_ms = 33
        self.victory_video_candidates = [
            os.path.join("assets", "video", "shimiya.mp4"),
            "shimiya.mp4",
        ]
        self.victory_video_audio_candidates = [
            os.path.join("assets", "audio", "shimiya.wav"),
            os.path.join("assets", "audio", "shimiya.mp3"),
            os.path.join("assets", "audio", "shimiya.ogg"),
            "shimiya.wav",
            "shimiya.mp3",
            "shimiya.ogg",
        ]
        self.victory_video_path = None
        self.victory_video_cap = None
        self.victory_video_audio_started = False
        self.victory_video_started_at = 0
        self.victory_video_last_frame_at = 0
        self.victory_video_frame_delay_ms = 33
        self.endgame_video_candidates = [
            os.path.join("assets", "video", "endgame_scene.mkv"),
            os.path.join("assets", "video", "endgame_scene.mp4"),
            "endgame_scene.mkv",
            "endgame_scene.mp4",
        ]
        self.endgame_video_audio_candidates = [
            os.path.join("assets", "audio", "endgame_scene.wav"),
            os.path.join("assets", "audio", "endgame_scene.mp3"),
            os.path.join("assets", "audio", "endgame_scene.ogg"),
            "endgame_scene.wav",
            "endgame_scene.mp3",
            "endgame_scene.ogg",
        ]
        self.endgame_video_path = None
        self.endgame_video_cap = None
        self.endgame_video_audio_started = False
        self.endgame_video_started_at = 0
        self.endgame_video_last_frame_at = 0
        self.endgame_video_frame_delay_ms = 33
        self.credits_video_candidates = [
            os.path.join("assets", "video", "credits.mkv"),
            os.path.join("assets", "video", "credits.mp4"),
            "credits.mkv",
            "credits.mp4",
        ]
        self.credits_video_audio_candidates = [
            os.path.join("assets", "audio", "credits.wav"),
            os.path.join("assets", "audio", "credits.mp3"),
            os.path.join("assets", "audio", "credits.ogg"),
            "credits.wav",
            "credits.mp3",
            "credits.ogg",
        ]
        self.credits_video_path = None
        self.credits_video_cap = None
        self.credits_video_audio_started = False
        self.credits_video_started_at = 0
        self.credits_video_last_frame_at = 0
        self.credits_video_frame_delay_ms = 33
        self.credits_audio_base_volume = 1.0
        self.credits_roll_speed_px_s = 46
        self.credits_roll_end_delay_ms = 3200
        self.credits_roll_script = self._build_credits_script(self.language)
        self.menu_video_candidates = [
            os.path.join("assets", "video", "menu.mkv"),
            os.path.join("assets", "video", "menu.mp4"),
            "menu.mkv",
            "menu.mp4",
        ]
        self.menu_video_path = None
        self.menu_video_cap = None
        self.menu_video_last_surface = None
        self.menu_video_last_frame_at = 0
        self.menu_video_frame_delay_ms = 33
        self._admin_pause_active = False
        self._admin_pause_started_at = 0

        self._rebuild_menu_layout()
        self._rebuild_settings_layout()

        self._load_progress()
        self._load_menu_video()

    def _get_cursor_path_for_size(self, size):
        return os.path.join("assets", "images", f"cursor{int(size)}.png")

    def tr(self, key, **kwargs):
        lang = str(getattr(self, "language", "en") or "en").lower()
        pack = self.TRANSLATIONS.get(lang, self.TRANSLATIONS.get("en", {}))
        fallback = self.TRANSLATIONS.get("en", {})
        template = pack.get(key, fallback.get(key, key))
        try:
            return str(template).format(**kwargs)
        except Exception:
            return str(template)

    def _build_credits_script(self, language):
        if str(language).lower() == "it":
            return [
                {"type": "title", "text": "Five Nights at The Corrupted Lab"},
                {"type": "subtitle", "text": "Titoli di coda"},
                {"type": "space"},
                {"type": "header", "text": "Origine del progetto"},
                {
                    "type": "name",
                    "text": "Parodia dichiarata",
                    "detail": "Il gioco nasce come parodia del gioco 'Five Nights at Freddy's 3'. L'obiettivo non è replicare l'opera originale, ma reinterpretarne alcune atmosfere con tono ironico, ambientazione scolastica e personaggi volutamente sopra le righe.",
                },
                {
                    "type": "name",
                    "text": "Identita propria",
                    "detail": "Pur partendo da un riferimento noto, il progetto sviluppa una propria identita attraverso interfaccia, gestione errori di sistema, ritmo delle notti, assets selezionati dal team e una costruzione narrativa orientata alla parodia.",
                },
                {"type": "space"},
                {"type": "header", "text": "Direzione creativa e visione del progetto"},
                {
                    "type": "name",
                    "text": "Team Gioco Scuola",
                    "detail": "Il progetto e nato con l'obiettivo di costruire un'esperienza horror scolastica leggibile, tesa e giocabile anche in sessioni brevi. Ogni scelta su ritmo, atmosfera e interfaccia e stata fatta per mantenere alta la pressione senza perdere chiarezza.",
                },
                {"type": "space"},
                {"type": "header", "text": "Sviluppo codice e logica di gioco"},
                {
                    "type": "name",
                    "text": "Gabriele Bella",
                    "detail": "Ha definito l'architettura del codice separando rendering, flusso di gioco, input e sistemi. Ha implementato il loop principale, la progressione notturna, la gestione degli stati e la logica degli animatronics, bilanciando tempi di attacco, finestre di reazione e pressione crescente tra le notti.",
                },
                {
                    "type": "name",
                    "text": "Sistemi di gameplay",
                    "detail": "Sotto la sua guida sono stati integrati torcia, pannello sistemi, gestione errori, trigger camera e sequenze di salto tra schermate, con particolare attenzione alla coerenza tra feedback audio-visivo e conseguenze di gioco.",
                },
                {"type": "space"},
                {"type": "header", "text": "Selezione immagini e suoni"},
                {
                    "type": "name",
                    "text": "Flavio Cosimo Cigna",
                    "detail": "Ha curato ricerca, selezione e organizzazione del materiale visivo e sonoro. Ha contribuito a costruire un'identita riconoscibile scegliendo sprite, sfondi, effetti e musiche in modo coerente con il tono del gioco, mantenendo leggibilita nelle scene piu cariche.",
                },
                {
                    "type": "name",
                    "text": "Direzione audio-visiva",
                    "detail": "Ha supportato la costruzione dell'atmosfera con una scelta mirata di transizioni, rumori ambientali e suoni di feedback, fondamentali per suggerire pericolo, movimento e urgenza senza interrompere il flusso del gameplay.",
                },
                {"type": "space"},
                {"type": "header", "text": "Stesura credits finali"},
                {
                    "type": "name",
                    "text": "Javeria Amin",
                    "detail": "Ha redatto, ordinato e armonizzato i testi dei crediti finali, valorizzando con chiarezza i ruoli del team e trasformando la chiusura del gioco in una parte narrativa coerente con il resto dell'esperienza.",
                },
                {
                    "type": "name",
                    "text": "Revisione e impaginazione",
                    "detail": "Ha lavorato su tono, leggibilita e ritmo dei testi per rendere i crediti scorrevoli, comprensibili e rispettosi del contributo di ogni membro, mantenendo un linguaggio lineare e accessibile.",
                },
                {"type": "space"},
                {"type": "header", "text": "Ringraziamenti"},
                {
                    "type": "name",
                    "text": "A chi ha testato il progetto",
                    "detail": "Un ringraziamento speciale a chi ha provato il gioco, segnalato problemi, dato suggerimenti e aiutato a rifinire difficolta, tempi e feedback. Ogni test ha contribuito a migliorare stabilita e qualita dell'esperienza finale.",
                },
                {"type": "space"},
                {"type": "subtitle", "text": "Grazie per aver giocato"},
                {"type": "subtitle", "text": "Ci vediamo alla prossima notte"},
            ]

        return [
            {"type": "title", "text": "Five Nights at The Corrupted Lab"},
            {"type": "subtitle", "text": "Credits"},
            {"type": "space"},
            {"type": "header", "text": "Project origin"},
            {
                "type": "name",
                "text": "Declared parody",
                "detail": "This game was born as a parody of 'Five Nights at Freddy's 3'. The intent is not to replicate the original work, but to reinterpret part of its atmosphere with an ironic tone, a school setting, and intentionally over-the-top characters.",
            },
            {
                "type": "name",
                "text": "Own identity",
                "detail": "Even with a recognizable inspiration, the project builds its own identity through interface choices, system-error management, night pacing, team-curated assets, and a narrative style explicitly oriented toward parody.",
            },
            {"type": "space"},
            {"type": "header", "text": "Creative direction and project vision"},
            {
                "type": "name",
                "text": "Gioco Scuola Team",
                "detail": "The project was designed to deliver a readable and tense school-horror experience, enjoyable even in short sessions. Every choice about rhythm, atmosphere and interface was made to keep pressure high without sacrificing clarity.",
            },
            {"type": "space"},
            {"type": "header", "text": "Code development and gameplay logic"},
            {
                "type": "name",
                "text": "Gabriele Bella",
                "detail": "He designed the code architecture by separating rendering, flow, input and systems. He implemented the core loop, night progression, state handling and animatronic logic, balancing attack timing, reaction windows and pressure growth across nights.",
            },
            {
                "type": "name",
                "text": "Gameplay systems",
                "detail": "Under his direction, flashlight, systems panel, error handling, camera triggers and state transitions were integrated with a focus on coherence between audiovisual feedback and gameplay consequences.",
            },
            {"type": "space"},
            {"type": "header", "text": "Visual and audio asset selection"},
            {
                "type": "name",
                "text": "Flavio Cosimo Cigna",
                "detail": "He curated research, selection and organization of visual and audio assets. He helped shape a recognizable identity through coherent sprite, background, effects and music choices, while preserving readability in dense scenes.",
            },
            {
                "type": "name",
                "text": "Audiovisual direction",
                "detail": "He supported atmosphere building with deliberate transitions, ambient noises and feedback sounds, essential to suggest danger, movement and urgency without interrupting gameplay flow.",
            },
            {"type": "space"},
            {"type": "header", "text": "Final credits writing"},
            {
                "type": "name",
                "text": "Javeria Amin",
                "detail": "She wrote, organized and refined the final credit text, clearly highlighting team roles and turning the ending into a narrative moment aligned with the rest of the experience.",
            },
            {
                "type": "name",
                "text": "Revision and layout",
                "detail": "She refined tone, readability and text rhythm to make credits smooth, understandable and respectful of each contributor, keeping language clear and accessible.",
            },
            {"type": "space"},
            {"type": "header", "text": "Special thanks"},
            {
                "type": "name",
                "text": "To everyone who tested the game",
                "detail": "A special thanks to everyone who played the game, reported issues, shared suggestions and helped refine difficulty, timing and feedback. Every test improved the final stability and overall experience quality.",
            },
            {"type": "space"},
            {"type": "subtitle", "text": "Thanks for playing"},
            {"type": "subtitle", "text": "See you on the next night"},
        ]

    def _read_settings_data(self):
        try:
            with open(self.settings_save_path, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except (OSError, ValueError, json.JSONDecodeError):
            return {}

        if not isinstance(payload, dict):
            return {}
        return payload

    def _load_settings(self):
        settings = self._read_settings_data()
        if not settings:
            return

        mode = str(settings.get("display_mode", self.display_mode)).lower()
        if mode in self.display_mode_options:
            self.display_mode = mode

        size_raw = settings.get("window_size", self.window_size)
        if isinstance(size_raw, (list, tuple)) and len(size_raw) == 2:
            try:
                parsed_size = (int(size_raw[0]), int(size_raw[1]))
            except (TypeError, ValueError):
                parsed_size = None
            if parsed_size is not None:
                if parsed_size not in self.window_size_options:
                    self.window_size_options.append(parsed_size)
                    self.window_size_options = sorted(set(self.window_size_options), key=lambda s: (s[0] * s[1], s[0]))
                self.window_size = parsed_size

        try:
            cursor_size = int(settings.get("cursor_size", self.selected_cursor_size))
        except (TypeError, ValueError):
            cursor_size = self.selected_cursor_size
        if cursor_size in self.cursor_size_options:
            self.selected_cursor_size = cursor_size

        language = str(settings.get("language", self.language)).lower()
        if language in self.language_options:
            self.language = language

    def save_settings(self):
        payload = {
            "schema_version": 1,
            "display_mode": self.display_mode,
            "window_size": [int(self.window_size[0]), int(self.window_size[1])],
            "cursor_size": int(self.selected_cursor_size),
            "language": self.language,
        }

        try:
            with open(self.settings_save_path, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, ensure_ascii=True, indent=2)
        except OSError:
            return False
        return True

    def _apply_display_mode(self):
        mode = str(getattr(self, "display_mode", "windowed") or "windowed").lower()
        if mode not in self.display_mode_options:
            mode = "windowed"
            self.display_mode = mode

        target_w, target_h = tuple(getattr(self, "window_size", (self.width, self.height)))
        target_w = max(800, int(target_w))
        target_h = max(600, int(target_h))

        if mode == "fullscreen":
            fullscreen_size = (target_w, target_h)
            modes = pygame.display.list_modes()
            if modes and modes != -1:
                supported = [m for m in modes if m[0] >= 800 and m[1] >= 600]
                if supported:
                    fullscreen_size = min(
                        supported,
                        key=lambda m: abs(m[0] - target_w) + abs(m[1] - target_h),
                    )
            target_w, target_h = int(fullscreen_size[0]), int(fullscreen_size[1])
            flags = pygame.FULLSCREEN
        elif mode == "windowed_borderless":
            os.environ["SDL_VIDEO_CENTERED"] = "1"
            flags = pygame.NOFRAME
        else:
            flags = 0

        try:
            self.screen = pygame.display.set_mode((target_w, target_h), flags)
        except pygame.error:
            fallback_size = (target_w, target_h)
            fallback_flags = 0
            if mode == "fullscreen":
                info = pygame.display.Info()
                fallback_size = (
                    max(800, int(getattr(info, "current_w", target_w) or target_w)),
                    max(600, int(getattr(info, "current_h", target_h) or target_h)),
                )
                fallback_flags = pygame.FULLSCREEN
            self.screen = pygame.display.set_mode(fallback_size, fallback_flags)

        actual_w, actual_h = self.screen.get_size()
        self.width = int(actual_w)
        self.height = int(actual_h)
        self._refresh_runtime_layout()
        self._sync_custom_cursor_visibility()

    def _refresh_runtime_layout(self):
        if not hasattr(self, "base_background"):
            return

        self.menu_background = pygame.transform.scale(self.base_background, (self.width, self.height))
        self.game_background = pygame.transform.scale(self.base_background, (int(self.width * 1.7), self.height))

        old_camera = getattr(self, "camera", None)
        old_offset = float(getattr(old_camera, "offset_x", 0.0)) if old_camera is not None else 0.0
        old_smoothing = float(getattr(old_camera, "smoothing", 0.13)) if old_camera is not None else 0.13
        self.camera = Camera(self.width, self.game_background.get_width(), smoothing=old_smoothing)
        self.camera.offset_x = max(0.0, min(float(self.camera.max_offset), old_offset))

        old_flashlight = getattr(self, "flashlight", None)
        radius = int(getattr(old_flashlight, "radius", 120)) if old_flashlight is not None else 120
        alpha = int(getattr(old_flashlight, "alpha", 200)) if old_flashlight is not None else 200
        self.flashlight = Flashlight(self.width, self.height, radius=radius, alpha=alpha)

        if hasattr(self, "video_camere"):
            self.video_camere.width = self.width
            self.video_camere.height = self.height
            panel_w = min(1420, max(1080, int(self.width * 0.72)))
            panel_h = min(820, max(680, int(self.height * 0.78)))
            panel_x = max(0, self.width - panel_w)
            panel_y = max(56, (self.height - panel_h) // 2 + 8)
            self.video_camere.set_panel_rect(panel_x, panel_y, panel_w, panel_h)
            self.video_camere.set_trigger_rect(
                x=self.width - 92,
                y=self.height / 2 - 255,
                w=82,
                h=210,
            )

        if hasattr(self, "system_panel"):
            self.system_panel.width = self.width
            self.system_panel.height = self.height
            panel_w = min(int(self.width * 0.86), 980)
            panel_h = min(int(self.height * 0.84), 780)
            panel_x = max(18, (self.width - panel_w) // 2)
            panel_y = max(16, (self.height - panel_h) // 2)
            self.system_panel.panel_rect = pygame.Rect(panel_x, panel_y, panel_w, panel_h)
            self.system_panel.set_trigger_rect(
                x=18,
                y=self.height - 94,
                w=210,
                h=82,
            )

        self._rebuild_menu_layout()
        self._rebuild_settings_layout()

    def _rebuild_menu_layout(self):
        button_width, button_height = 380, 78
        button_gap = 14
        left_x = int(self.width * 0.08)
        start_y = self.height // 2 - 122
        self.new_game_button = pygame.Rect(left_x, start_y, button_width, button_height)
        self.continue_button = pygame.Rect(left_x, start_y + (button_height + button_gap), button_width, button_height)
        self.credits_button = pygame.Rect(left_x, start_y + ((button_height + button_gap) * 2), button_width, button_height)
        self.settings_button = pygame.Rect(left_x, start_y + ((button_height + button_gap) * 3), button_width, button_height)
        self.exit_button = pygame.Rect(left_x, start_y + ((button_height + button_gap) * 4), button_width, button_height)

    def _rebuild_settings_layout(self):
        panel_w = min(1320, int(self.width * 0.84))
        panel_h = min(820, int(self.height * 0.82))
        panel_x = (self.width - panel_w) // 2
        panel_y = (self.height - panel_h) // 2
        self.settings_panel_rect = pygame.Rect(panel_x, panel_y, panel_w, panel_h)

        opt_w = 250
        opt_h = 58
        gap = 16
        group_gap = 92
        start_x = panel_x + 44
        y = panel_y + 146

        self.settings_display_mode_buttons = {}
        for idx, mode in enumerate(self.display_mode_options):
            x = start_x + (idx * (opt_w + gap))
            self.settings_display_mode_buttons[mode] = pygame.Rect(x, y, opt_w, opt_h)

        y += opt_h + group_gap
        self.settings_window_size_buttons = {}
        for idx, size in enumerate(self.window_size_options):
            x = start_x + (idx * (opt_w + gap))
            self.settings_window_size_buttons[size] = pygame.Rect(x, y, opt_w, opt_h)

        y += opt_h + group_gap
        self.settings_cursor_size_buttons = {}
        for idx, size in enumerate(self.cursor_size_options):
            x = start_x + (idx * (opt_w + gap))
            self.settings_cursor_size_buttons[size] = pygame.Rect(x, y, opt_w, opt_h)

        y += opt_h + group_gap
        self.settings_language_buttons = {}
        for idx, language in enumerate(self.language_options):
            x = start_x + (idx * (opt_w + gap))
            self.settings_language_buttons[language] = pygame.Rect(x, y, opt_w, opt_h)

        self.settings_back_button = pygame.Rect(panel_x + panel_w - 230, panel_y + panel_h - 88, 190, 52)

    def set_display_mode(self, mode):
        mode = str(mode).lower()
        if mode not in self.display_mode_options:
            return False
        self.display_mode = mode
        self._apply_display_mode()
        self.save_settings()
        return True

    def set_window_size(self, size):
        if size not in self.window_size_options:
            return False
        self.window_size = tuple(size)
        self._apply_display_mode()
        self.save_settings()
        return True

    def set_cursor_size(self, size):
        try:
            size = int(size)
        except (TypeError, ValueError):
            return False

        if size not in self.cursor_size_options:
            return False

        self.selected_cursor_size = size
        self.custom_cursor_path = self._get_cursor_path_for_size(size)
        if self._load_custom_cursor():
            self.save_settings()
            return True

        self.custom_cursor_path = self.cursor_fallback_path
        loaded = self._load_custom_cursor()
        if loaded:
            self.save_settings()
        return loaded

    def set_language(self, language):
        language = str(language).lower()
        if language not in self.language_options:
            return False
        self.language = language
        self.credits_roll_script = self._build_credits_script(self.language)
        self.loading_message = self.tr("loading.default")
        self.save_settings()
        return True

    def toggle_fullscreen(self):
        if self.display_mode == "fullscreen":
            self.display_mode = "windowed"
        else:
            self.display_mode = "fullscreen"
        self._apply_display_mode()
        self.save_settings()
