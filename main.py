import os
import sys
import json
import ctypes

import pygame

from modules.game import Game


def _load_window_appearance_settings():
    settings_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json")
    defaults = {
        "titlebar_theme": "dark",
        "window_icon": os.path.join("assets", "images", "logo.png"),
        "taskbar_icon": os.path.join("assets", "images", "logo.ico"),
        "windows_app_id": "FiveNights.CorruptedLab",
    }

    if not os.path.isfile(settings_path):
        return defaults

    try:
        with open(settings_path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, ValueError, json.JSONDecodeError):
        return defaults

    if not isinstance(payload, dict):
        return defaults

    theme = str(payload.get("titlebar_theme", defaults["titlebar_theme"]) or "").strip().lower()
    if theme not in ("dark", "light"):
        theme = defaults["titlebar_theme"]

    icon_path = str(payload.get("window_icon", defaults["window_icon"]) or "").strip()
    if not icon_path:
        icon_path = defaults["window_icon"]

    taskbar_icon = str(payload.get("taskbar_icon", defaults["taskbar_icon"]) or "").strip()
    if not taskbar_icon:
        taskbar_icon = defaults["taskbar_icon"]

    app_id = str(payload.get("windows_app_id", defaults["windows_app_id"]) or "").strip()
    if not app_id:
        app_id = defaults["windows_app_id"]

    # If a dedicated ICO is not configured, try same-name .ico beside window_icon.
    if not os.path.isfile(taskbar_icon) and icon_path:
        base, _ = os.path.splitext(icon_path)
        ico_candidate = f"{base}.ico"
        if os.path.isfile(ico_candidate):
            taskbar_icon = ico_candidate

    return {
        "titlebar_theme": theme,
        "window_icon": icon_path,
        "taskbar_icon": taskbar_icon,
        "windows_app_id": app_id,
    }


def _set_windows_app_id(app_id):
    if os.name != "nt":
        return

    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(str(app_id))
    except Exception:
        pass


def _set_windows_dpi_awareness():
    if os.name != "nt":
        return

    try:
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass


def _apply_window_icon(icon_path):
    if not icon_path:
        return
    if not os.path.isfile(icon_path):
        return

    try:
        icon_surface = pygame.image.load(icon_path)
        pygame.display.set_icon(icon_surface)
    except Exception:
        pass


def _apply_windows_titlebar_theme(theme):
    if os.name != "nt":
        return

    try:
        wm_info = pygame.display.get_wm_info()
        hwnd = int(wm_info.get("window", 0) or 0)
        if hwnd <= 0:
            return

        value = ctypes.c_int(1 if str(theme).lower() == "dark" else 0)
        dwm_set_attr = ctypes.windll.dwmapi.DwmSetWindowAttribute

        # DWMWA_USE_IMMERSIVE_DARK_MODE: 20 on newer Windows, 19 on older builds.
        for attr in (20, 19):
            result = dwm_set_attr(
                ctypes.c_void_p(hwnd),
                ctypes.c_uint(attr),
                ctypes.byref(value),
                ctypes.sizeof(value),
            )
            if result == 0:
                break
    except Exception:
        pass


def _apply_windows_taskbar_icon(icon_path):
    if os.name != "nt":
        return
    if not icon_path or not os.path.isfile(icon_path):
        return

    try:
        wm_info = pygame.display.get_wm_info()
        hwnd = int(wm_info.get("window", 0) or 0)
        if hwnd <= 0:
            return

        # Win32 constants
        WM_SETICON = 0x0080
        ICON_SMALL = 0
        ICON_BIG = 1
        IMAGE_ICON = 1
        LR_LOADFROMFILE = 0x0010
        LR_DEFAULTSIZE = 0x0040

        load_image = ctypes.windll.user32.LoadImageW
        send_message = ctypes.windll.user32.SendMessageW

        hicon = load_image(
            None,
            ctypes.c_wchar_p(os.path.abspath(icon_path)),
            IMAGE_ICON,
            0,
            0,
            LR_LOADFROMFILE | LR_DEFAULTSIZE,
        )
        if not hicon:
            return

        send_message(ctypes.c_void_p(hwnd), WM_SETICON, ICON_SMALL, hicon)
        send_message(ctypes.c_void_p(hwnd), WM_SETICON, ICON_BIG, hicon)
    except Exception:
        pass


def main():
    # In PyInstaller --onefile, bundled files are unpacked in _MEIPASS.
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        os.chdir(sys._MEIPASS)

    window_appearance = _load_window_appearance_settings()
    _set_windows_app_id(window_appearance.get("windows_app_id", "FiveNights.CorruptedLab"))
    _set_windows_dpi_awareness()

    pygame.init()
    _apply_window_icon(window_appearance.get("window_icon", ""))

    game = Game(width=1920, height=1080)
    _apply_windows_taskbar_icon(window_appearance.get("taskbar_icon", ""))
    _apply_windows_titlebar_theme(window_appearance.get("titlebar_theme", "dark"))
    game.run()


if __name__ == "__main__":
    main()
