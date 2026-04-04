# Gioco Scuola

Gioco horror in stile survival-notturno realizzato con Pygame.

Scopo: sopravvivere fino alle 6:00 monitorando telecamere, condotti, errori di sistema e gestione torcia.

## Requisiti

- Python 3.10+ (consigliato 3.11)
- Windows (supportato), con supporto audio attivo

Dipendenze Python principali:

- `pygame`
- `opencv-python`

## Installazione

```bash
python -m venv .venv
.venv\Scripts\activate
pip install pygame opencv-python
```

## Avvio del gioco

```bash
python main.py
```

## Controlli principali

- `ENTER`: conferma nel menu / avanza schermate intro
- `SPACE`: torcia in ufficio
- `E`: skip video finali
- `M`: ritorna al menu durante la partita
- `ESC`: chiudi il gioco
- `F11` oppure `ALT+ENTER`: fullscreen on/off

Controlli monitor CAM:

- Click trigger `CAM` a destra: apri/chiudi monitor
- `TAB` nel monitor: switch mappa principale / condotti
- In mappa condotti: doppio click su una tratta per chiuderla/aprirla

## Flusso di gioco

1. Menu principale con video background
2. Intro notte
3. (Solo Notte 1) Tutorial iniziale con istruzioni rapide
4. Gameplay
5. Fine notte:
	- Notti 1-4: video vittoria
	- Notte 5: sequenza `endgame` e poi `credits`

## Sistemi principali

- Animatronics con percorsi camera/condotti
- Errori di sistema (camera, ventilazione, torcia)
- Reboot moduli dal pannello sinistro
- Torcia con durata/cooldown
- Jumpscare con video/audio

## Asset

Struttura importante:

- `assets/audio/` suoni e musica
- `assets/images/` sfondi, sprite e mappe camere
- `assets/video/` video menu, victory/defeat, endgame e credits

Note video:

- Il progetto usa OpenCV per i video.
- Se un formato non viene decodificato bene, preferire `.mp4`.

## Build EXE (Windows)

Per creare un eseguibile:

```bash
python build_exe.py
```

Lo script usa PyInstaller e include la cartella `assets/` nel bundle.

## Risoluzione problemi rapida

- Video menu lento: verificare codec del file video (`.mp4` consigliato)
- Audio assente: controllare output audio di Windows e file in `assets/audio/`
- Schermata nera CAM: verificare presenza immagini in `assets/images/cams/`