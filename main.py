import customtkinter as ctk
import ctypes
import sys
from src.app_controller import AppController
from src.ui.app_window import AppWindow

# Set AppUserModelID to ensure proper taskbar grouping
try:
    myappid = 'com.vkmusicsaver.app.1.0' # arbitrary string
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except Exception:
    pass

if __name__ == "__main__":
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")

    controller = AppController()

    app = AppWindow(controller)

    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()
