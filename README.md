# Gioco Scuola / School Game

## Italiano

### Descrizione

Gioco horror survival-notturno realizzato con Pygame.

Il progetto nasce come parodia del gioco "Five Nights at Freddy's 3": prende ispirazione da alcune atmosfere e meccaniche di tensione, ma le reinterpreta con ambientazione scolastica, tono ironico e identita propria.

Obiettivo: sopravvivere fino alle 6:00 monitorando telecamere, condotti, errori di sistema e gestione torcia.

### Requisiti

- Python 3.10+ (consigliato 3.11)
- Windows (supportato) con audio attivo

Dipendenze principali:

- `pygame`
- `opencv-python`

### Installazione

```bash
python -m venv .venv
.venv\Scripts\activate
pip install pygame opencv-python
```

### Avvio

```bash
python main.py
```

### Controlli

- `ENTER`: conferma menu / avanza schermate intro
- `SPACE`: torcia in ufficio
- `E`: saltare video finali
- `M`: torna al menu durante la partita
- `ESC`: chiude il gioco
- `F11` o `ALT+ENTER`: fullscreen on/off

Monitor CAM:

- Click sul trigger `CAM` a destra: apre/chiude monitor
- `TAB` nel monitor: cambia mappa principale/condotti
- In mappa condotti: doppio click su una tratta per chiuderla/aprirla

### Impostazioni disponibili

- Modalita schermo: windowed / borderless / fullscreen
- Risoluzione finestra
- Dimensione cursore: 32 / 48 / 64
- Lingua: Italiano / English
- Salvataggio automatico in `settings.json`

### Flusso di gioco

1. Menu principale
2. Intro notte
3. (Solo notte 1) tutorial
4. Gameplay
5. Fine notte:
   - Notti 1-4: video vittoria
   - Notte 5: endgame e poi credits

### Note asset

- `assets/audio/`: suoni e musica
- `assets/images/`: sfondi, sprite, mappe e cursori
- `assets/video/`: video menu, vittoria, sconfitta, endgame, credits

### Build EXE (Windows) - IT

```bash
python build_exe.py
```

### Troubleshooting rapido

- Video menu lento: preferire file `.mp4`
- Audio assente: verificare output Windows e file audio
- CAM nera: controllare immagini in `assets/images/cams/`

---

## English

### Description

Night-survival horror game built with Pygame.

This project was born as a parody of "Five Nights at Freddy's 3": it takes inspiration from part of its atmosphere and tension mechanics, then reinterprets them with a school setting, an ironic tone, and its own identity.

Goal: survive until 6:00 AM by managing cameras, vents, system errors, and flashlight timing.

### Requirements

- Python 3.10+ (3.11 recommended)
- Windows with active audio support

Main dependencies:

- `pygame`
- `opencv-python`

### Installation

```bash
python -m venv .venv
.venv\Scripts\activate
pip install pygame opencv-python
```

### Run

```bash
python main.py
```

### Controls

- `ENTER`: confirm menu / advance intro screens
- `SPACE`: flashlight in office
- `E`: skip ending videos
- `M`: return to menu during gameplay
- `ESC`: quit game
- `F11` or `ALT+ENTER`: fullscreen on/off

CAM monitor:

- Click the `CAM` trigger on the right: open/close monitor
- `TAB` in monitor: switch main/vent map
- In vent map: double click a segment to toggle close/open

### Available settings

- Display mode: windowed / borderless / fullscreen
- Window resolution
- Cursor size: 32 / 48 / 64
- Language: Italiano / English
- Auto-saved in `settings.json`

### Game flow

1. Main menu
2. Night intro
3. (Night 1 only) tutorial
4. Gameplay
5. Night ending:
   - Nights 1-4: victory video
   - Night 5: endgame, then credits

### Asset notes

- `assets/audio/`: sounds and music
- `assets/images/`: backgrounds, sprites, maps, cursors
- `assets/video/`: menu, victory, defeat, endgame, credits videos

### Build EXE (Windows) - EN

```bash
python build_exe.py
```

### Quick troubleshooting

- Slow menu video: prefer `.mp4` assets
- No audio: check Windows output and audio files
- Black CAM screen: verify files in `assets/images/cams/`
