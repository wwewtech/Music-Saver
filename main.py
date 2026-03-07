import customtkinter as ctk
from src.app_controller import AppController
from src.ui.app_window import AppWindow

if __name__ == "__main__":
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")

    controller = AppController()
    app = AppWindow(controller)

    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()
