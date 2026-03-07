import customtkinter as ctk
import ctypes
from src.app_controller import AppController
from src.app_config import APP_ID, UI_APPEARANCE_MODE, UI_COLOR_THEME
from src.ui.app_window import AppWindow

def _set_windows_app_id():
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_ID)
    except Exception:
        pass


def main():
    _set_windows_app_id()
    ctk.set_appearance_mode(UI_APPEARANCE_MODE)
    ctk.set_default_color_theme(UI_COLOR_THEME)

    controller = AppController()

    app = AppWindow(controller)
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()

if __name__ == "__main__":
    main()
