import customtkinter as ctk
from src.app_controller import AppController
from src.ui.app_window import AppWindow
from src.ui.wizard.setup_wizard import SetupWizard

if __name__ == "__main__":
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")

    controller = AppController()

    # Wizard Check
    if not controller.settings_manager.get("setup_completed", False):
        wizard = SetupWizard(controller)
        wizard.mainloop()
        
        # Ensure setup was marked done, else exit
        if not controller.settings_manager.get("setup_completed", False):
            exit()

    app = AppWindow(controller)

    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()
