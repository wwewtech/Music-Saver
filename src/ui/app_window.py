import customtkinter as ctk
import logging
from datetime import datetime

from src.ui.components.sidebar import SideBar
from src.ui.components.log_panel import LogPanel
from src.ui.components.playlist_view import PlaylistView


class AppWindow(ctk.CTk):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller

        # Configure Controller Callbacks
        self.controller.on_log = self.on_log_message
        self.controller.on_scan_complete = self.on_scan_complete
        self.controller.on_progress = self.on_progress_update
        self.controller.on_download_complete = self.on_download_finished
        self.controller.on_login_success = self.on_login_success
        self.geometry("1000x700")

        self.setup_ui()

    def setup_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # 1. Sidebar
        self.sidebar = SideBar(
            self,
            on_login=self.controller.start_browser_and_login,
            on_scan=self.controller.scan_playlists,
        )
        self.sidebar.grid(row=0, column=0, rowspan=2, sticky="nsew")
        # Telegram Init
        tg = self.controller.get_tg_settings()
        self.sidebar.set_tg_settings(tg.get('tg_bot_token'), tg.get('tg_chat_id'))
        
        def save_tg(token, chat_id):
            success, msg = self.controller.save_tg_settings(token, chat_id)
            self.on_log_message(msg)

        self.sidebar.on_save_callback = save_tg

        # 2. Main Area (Playlists)
        self.main_panel = ctk.CTkFrame(self, fg_color="transparent")
        self.main_panel.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        self.playlist_view = PlaylistView(self.main_panel)
        self.playlist_view.pack(fill="both", expand=True, pady=5)

        # 3. Bottom Panel (Actions + Log)
        self.bottom_panel = ctk.CTkFrame(self, height=150)
        self.bottom_panel.grid(row=1, column=1, sticky="ew", padx=10, pady=10)

        self.btn_download = ctk.CTkButton(
            self.bottom_panel,
            text="3. СКАЧАТЬ",
            command=self.action_download,
            state="disabled",
            fg_color="green",
            hover_color="darkgreen",
            height=40,
        )
        self.btn_download.pack(fill="x", padx=10, pady=5)

        self.progress_bar = ctk.CTkProgressBar(self.bottom_panel)
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x", padx=10, pady=5)

        self.log_panel = LogPanel(self.bottom_panel)
        self.log_panel.pack(fill="both", padx=10, pady=5)

    def action_download(self):
        selected = self.playlist_view.get_selected()
        if not selected:
            self.on_log_message("Выберите плейлист!")
            return

        settings = {
            "use_id3": self.sidebar.sw_tags.get(),
            "use_covers": self.sidebar.sw_covers.get(),
        }

        self.btn_download.configure(state="disabled", text="РАБОТАЮ...")
        self.controller.start_download(selected, settings)

    # --- Callbacks ---
    def on_log_message(self, msg):
        # Ensure thread safety for Tkinter
        self.after(0, lambda: self.log_panel.append_log(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}"))

    def on_login_success(self):
        self.after(0, lambda: self.sidebar.enable_scan_btn())
        self.on_log_message("Кнопка поиска плейлистов разблокирована.")

    def on_scan_complete(self, playlists):
        def _update():
            self.playlist_view.update_playlists(playlists)
            if playlists:
                self.btn_download.configure(state="normal")
                self.sidebar.enable_scan_btn()
            else:
                self.sidebar.enable_scan_btn()

        self.after(0, _update)

    def on_progress_update(self, val):
        self.after(0, lambda: self.progress_bar.set(val))

    def on_download_finished(self):
        self.after(
            0, lambda: self.btn_download.configure(state="normal", text="3. СКАЧАТЬ")
        )

    def setup_logging_pipe(self):
        # Optional: pipe standard logger to this GUI
        # For now, we rely on controller calling on_log
        pass

    def on_close(self):
        self.controller.close_app()
        self.destroy()
