import pygame


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

    game._draw_end_video_label(game.tr("menu.credits"), (180, 220, 255))
    skip_hint = game.font_small.render(game.tr("ui.press_e_skip"), True, (180, 220, 255))
    game.screen.blit(skip_hint, skip_hint.get_rect(bottomright=(game.width - 26, game.height - 24)))

    if fade_alpha > 0:
        fade_surface = pygame.Surface((game.width, game.height), pygame.SRCALPHA)
        fade_surface.fill((0, 0, 0, max(0, min(255, fade_alpha))))
        game.screen.blit(fade_surface, (0, 0))
