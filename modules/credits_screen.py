import pygame


def build_credits_script(language):
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
                "text": "Team Five Nights at Corrupted Lab",
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
                "text": "Javeeria Amin",
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
            "text": "Five Nights at Corrupted Lab Team",
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
            "text": "Javeeria Amin",
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


def draw_credits_video(game):
    now_ms = pygame.time.get_ticks()

    # Optional video background behind the rolling credits.
    if game.credits_video_cap is not None:
        frame_surface = game._read_synced_video_frame(
            game.credits_video_cap,
            game.credits_video_started_at,
            now_ms,
        )
        game.credits_video_last_frame_at = now_ms
        if frame_surface is not None:
            game.screen.blit(frame_surface, (0, 0))
        else:
            game.credits_video_cap = None

    if game.credits_video_cap is None:
        game.screen.fill((0, 0, 0))

    # Improve readability regardless of background.
    overlay = pygame.Surface((game.width, game.height), pygame.SRCALPHA)
    overlay.fill((4, 8, 16, 168))
    game.screen.blit(overlay, (0, 0))

    script = list(getattr(game, "credits_roll_script", []) or [])
    if not script:
        script = [
            {"type": "title", "text": game.tr("menu.credits")},
            {"type": "subtitle", "text": game.tr("credits.thanks")},
        ]

    elapsed_ms = max(0, now_ms - int(getattr(game, "credits_video_started_at", now_ms)))
    speed_px_s = max(20, int(getattr(game, "credits_roll_speed_px_s", 78)))
    scroll_offset = (elapsed_ms / 1000.0) * speed_px_s

    x_center = game.width // 2
    y = game.height + 80 - scroll_offset
    body_font = game.font_small

    for block in script:
        block_type = str(block.get("type", "name"))
        text = str(block.get("text", ""))

        if block_type == "space":
            y += 36
            continue

        if block_type == "title":
            surf = game.font_night.render(text, True, (214, 235, 255))
            shadow = game.font_night.render(text, True, (8, 12, 18))
            rect = surf.get_rect(center=(x_center, int(y)))
            game.screen.blit(shadow, rect.move(2, 2))
            game.screen.blit(surf, rect)
            y += 98
            continue

        if block_type == "subtitle":
            surf = game.font_hour.render(text, True, (176, 214, 255))
            shadow = game.font_hour.render(text, True, (6, 10, 16))
            rect = surf.get_rect(center=(x_center, int(y)))
            game.screen.blit(shadow, rect.move(2, 2))
            game.screen.blit(surf, rect)
            y += 74
            continue

        if block_type == "header":
            surf = body_font.render(text, True, (255, 214, 140))
            shadow = body_font.render(text, True, (20, 16, 8))
            rect = surf.get_rect(center=(x_center, int(y)))
            game.screen.blit(shadow, rect.move(2, 2))
            game.screen.blit(surf, rect)
            y += 46
            continue

        name_surf = body_font.render(text, True, (232, 240, 248))
        name_shadow = body_font.render(text, True, (10, 12, 16))
        name_rect = name_surf.get_rect(center=(x_center, int(y)))
        game.screen.blit(name_shadow, name_rect.move(2, 2))
        game.screen.blit(name_surf, name_rect)
        y += 36

        detail = str(block.get("detail", "")).strip()
        if detail:
            words = detail.split()
            line = []
            max_width = int(game.width * 0.76)
            lines = []
            for word in words:
                candidate = " ".join(line + [word]).strip()
                if body_font.size(candidate)[0] <= max_width:
                    line.append(word)
                else:
                    if line:
                        lines.append(" ".join(line))
                    line = [word]
            if line:
                lines.append(" ".join(line))

            for txt in lines:
                line_surf = body_font.render(txt, True, (176, 194, 214))
                line_shadow = body_font.render(txt, True, (8, 10, 14))
                line_rect = line_surf.get_rect(center=(x_center, int(y)))
                game.screen.blit(line_shadow, line_rect.move(2, 2))
                game.screen.blit(line_surf, line_rect)
                y += 34
            y += 16

    total_height = y + scroll_offset - (game.height + 80)
    finished_y = -max(180, int(getattr(game, "credits_roll_end_delay_ms", 1400) * speed_px_s / 1000.0))
    completion_metric = game.height + 80 - scroll_offset + total_height
    fade_start_y = finished_y + 220
    fade_alpha = 0
    if completion_metric < fade_start_y:
        fade_progress = min(1.0, max(0.0, (fade_start_y - completion_metric) / float(max(1, fade_start_y - finished_y))))
        fade_alpha = int(255 * fade_progress)

    if completion_metric < finished_y:
        game.enter_menu(play_click=False)
        return

    if getattr(game, "credits_video_audio_started", False):
        base_volume = float(getattr(game, "credits_audio_base_volume", 1.0))
        target_volume = base_volume * (1.0 - (max(0, min(255, fade_alpha)) / 255.0))
        game.audio.set_music_volume(target_volume)

    game._draw_end_video_label(game.tr("menu.credits"), (180, 220, 255))
    skip_hint = game.font_small.render(game.tr("ui.press_e_skip"), True, (180, 220, 255))
    game.screen.blit(skip_hint, skip_hint.get_rect(bottomright=(game.width - 26, game.height - 24)))

    if fade_alpha > 0:
        fade_surface = pygame.Surface((game.width, game.height), pygame.SRCALPHA)
        fade_surface.fill((0, 0, 0, max(0, min(255, fade_alpha))))
        game.screen.blit(fade_surface, (0, 0))
