import customtkinter as ctk
from tkinter import TclError
from queue import Queue, Empty
from src.ui.views.dashboard_view import DashboardView
from src.ui.views.downloader_view import DownloaderView
from src.ui.views.telegram_view import TelegramView
from src.ui.views.logs_view import LogsView
from src.ui.i18n import I18n


class AppWindow(ctk.CTk):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.theme = {
            "font": "Segoe UI Variable Display",
            "font_fallback": "Segoe UI",
            "bg": "#070b14",
            "panel": "#0d1424",
            "card": "#111a2e",
            "surface": "#0f172a",
            "text": "#f1f5f9",
            "muted": "#9ca3af",
            "accent": "#3b82f6",
            "accent_hover": "#2563eb",
            "success": "#16a34a",
            "border": "#1f2a44",
            "nav_idle": "#111a2e",
            "nav_hover": "#17233d",
        }

        lang = self.controller.get_language() if hasattr(self.controller, "get_language") else "ru"
        self.i18n = I18n(lang)
        self.i18n.subscribe(self.apply_language)
        self._ui_events = Queue()
        self._after_ids = set()
        self._is_closing = False
        self.current_view = "dashboard"
        self.view_titles = {
            "dashboard": ("dashboard.title", "dashboard.subtitle"),
            "vk": ("downloader.title", "downloader.subtitle"),
            "tg": ("telegram.title", "telegram.subtitle"),
            "logs": ("logs.title", "logs.subtitle"),
        }
        
        self.title(self.i18n.t("app.title"))
        self.geometry("1240x820")
        self.minsize(1120, 760)
        self.configure(fg_color=self.theme["bg"])
        
        # Configure Controller Callbacks
        self.controller.on_log = lambda msg: self._ui_events.put(("log", msg))
        self.controller.on_scan_complete = lambda playlists: self._ui_events.put(("scan_complete", playlists))
        self.controller.on_progress = lambda val: self._ui_events.put(("progress", val))
        self.controller.on_download_complete = lambda: self._ui_events.put(("download_complete", None))
        self.controller.on_login_success = lambda: self._ui_events.put(("login_success", None))
        
        # Hook for strategy
        self.controller.get_current_strategy = self.get_strategy_from_ui
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        
        self.setup_sidebar()
        self.setup_views()
        
        # Start Clock/Stats Loop
        self.update_stats_loop()
        self.process_ui_events()

    def _window_alive(self):
        try:
            return bool(self.winfo_exists())
        except TclError:
            return False

    def _schedule_after(self, delay_ms, callback):
        if self._is_closing or not self._window_alive():
            return None

        after_id = None

        def _wrapped():
            if after_id is not None:
                self._after_ids.discard(after_id)
            if self._is_closing or not self._window_alive():
                return
            callback()

        try:
            after_id = self.after(delay_ms, _wrapped)
            self._after_ids.add(after_id)
            return after_id
        except TclError:
            return None

    def _cancel_after_callbacks(self):
        for after_id in list(self._after_ids):
            try:
                self.after_cancel(after_id)
            except TclError:
                pass
            finally:
                self._after_ids.discard(after_id)

    def setup_sidebar(self):
        self.sidebar = ctk.CTkFrame(
            self,
            width=280,
            corner_radius=0,
            fg_color=self.theme["panel"],
            border_width=1,
            border_color=self.theme["border"],
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        brand_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        brand_frame.pack(fill="x", padx=18, pady=(28, 10))
        
        self.lbl_logo = ctk.CTkLabel(
            brand_frame,
            text=self.i18n.t("app.logo"),
            font=ctk.CTkFont(family=self.theme["font"], size=24, weight="bold"),
            text_color=self.theme["text"],
            anchor="w",
        )
        self.lbl_logo.pack(fill="x")

        self.lbl_logo_sub = ctk.CTkLabel(
            brand_frame,
            text=self.i18n.t("app.logo.subtitle"),
            font=ctk.CTkFont(family=self.theme["font_fallback"], size=12),
            text_color=self.theme["muted"],
            anchor="w",
        )
        self.lbl_logo_sub.pack(fill="x", pady=(2, 0))

        nav_block = ctk.CTkFrame(
            self.sidebar,
            fg_color=self.theme["card"],
            corner_radius=16,
            border_width=1,
            border_color=self.theme["border"],
        )
        nav_block.pack(fill="x", padx=14, pady=(16, 10))

        self.lbl_lang = ctk.CTkLabel(
            nav_block,
            text=self.i18n.t("app.lang"),
            font=ctk.CTkFont(family=self.theme["font"], size=13),
            text_color=self.theme["muted"],
            anchor="w",
        )
        self.lbl_lang.pack(fill="x", padx=12, pady=(12, 2))

        self.lang_switch = ctk.CTkSegmentedButton(
            nav_block,
            values=["RU", "EN"],
            command=self.on_language_change,
            selected_color=self.theme["accent"],
            selected_hover_color=self.theme["accent_hover"],
            unselected_color="#1f2a44",
            unselected_hover_color="#26365a",
            text_color=self.theme["text"],
            corner_radius=10,
            font=ctk.CTkFont(family=self.theme["font"], size=12, weight="bold"),
        )
        self.lang_switch.pack(fill="x", padx=12, pady=(4, 12))
        self.lang_switch.set("RU" if self.i18n.language == "ru" else "EN")
        
        self.btn_dash = self.create_nav_btn(nav_block, self.i18n.t("nav.dashboard"), "dashboard")
        self.btn_vk = self.create_nav_btn(nav_block, self.i18n.t("nav.downloader"), "vk")
        self.btn_tg = self.create_nav_btn(nav_block, self.i18n.t("nav.telegram"), "tg")
        self.btn_logs = self.create_nav_btn(nav_block, self.i18n.t("nav.logs"), "logs")
        
        # Small footer
        self.lbl_ver = ctk.CTkLabel(
            self.sidebar,
            text=self.i18n.t("app.version"),
            text_color=self.theme["muted"],
            font=ctk.CTkFont(family=self.theme["font_fallback"], size=11),
        )
        self.lbl_ver.pack(side="bottom", pady=14)

    def create_nav_btn(self, parent, text, view_name):
        btn = ctk.CTkButton(
            parent,
            text=text,
            fg_color=self.theme["nav_idle"],
            text_color=self.theme["text"],
            hover_color=self.theme["nav_hover"],
            anchor="w",
            corner_radius=12,
            border_spacing=14,
            height=46,
            font=ctk.CTkFont(family=self.theme["font_fallback"], size=14, weight="bold"),
            command=lambda: self.show_view(view_name),
        )
        btn.pack(fill="x", padx=10, pady=4)
        return btn

    def setup_views(self):
        self.main_area = ctk.CTkFrame(self, fg_color="transparent")
        self.main_area.grid(row=0, column=1, sticky="nsew", padx=14, pady=14)
        self.main_area.grid_rowconfigure(1, weight=1)
        self.main_area.grid_columnconfigure(0, weight=1)

        self.topbar = ctk.CTkFrame(
            self.main_area,
            fg_color=self.theme["surface"],
            corner_radius=16,
            border_width=1,
            border_color=self.theme["border"],
            height=88,
        )
        self.topbar.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        self.topbar.grid_columnconfigure(0, weight=1)

        self.lbl_section = ctk.CTkLabel(
            self.topbar,
            text="",
            font=ctk.CTkFont(family=self.theme["font"], size=24, weight="bold"),
            text_color=self.theme["text"],
            anchor="w",
        )
        self.lbl_section.grid(row=0, column=0, sticky="w", padx=18, pady=(14, 0))

        self.lbl_section_sub = ctk.CTkLabel(
            self.topbar,
            text="",
            font=ctk.CTkFont(family=self.theme["font_fallback"], size=12),
            text_color=self.theme["muted"],
            anchor="w",
        )
        self.lbl_section_sub.grid(row=1, column=0, sticky="w", padx=18, pady=(0, 12))

        self.view_container = ctk.CTkFrame(self.main_area, fg_color="transparent")
        self.view_container.grid(row=1, column=0, sticky="nsew")
        self.view_container.grid_rowconfigure(0, weight=1)
        self.view_container.grid_columnconfigure(0, weight=1)
        
        self.views = {}
        self.views["dashboard"] = DashboardView(self.view_container, self.controller, self.i18n, self.theme)
        self.views["vk"] = DownloaderView(self.view_container, self.controller, self.i18n, self.theme)
        self.views["tg"] = TelegramView(self.view_container, self.controller, self.i18n, self.theme)
        self.views["logs"] = LogsView(self.view_container, self.i18n, self.theme)
        
        # Init default
        self.show_view("dashboard")

    def show_view(self, name):
        self.current_view = name
        # Hide all
        for v in self.views.values():
            v.grid_forget()
        
        # Reset butons
        for btn in [self.btn_dash, self.btn_vk, self.btn_tg, self.btn_logs]:
            btn.configure(fg_color=self.theme["nav_idle"], hover_color=self.theme["nav_hover"])
            
        # Highlight active
        btn_map = {
            "dashboard": self.btn_dash,
            "vk": self.btn_vk,
            "tg": self.btn_tg,
            "logs": self.btn_logs
        }
        if name in btn_map:
            btn_map[name].configure(fg_color=self.theme["accent"], hover_color=self.theme["accent_hover"])

        title_key, subtitle_key = self.view_titles.get(name, ("dashboard.title", "dashboard.subtitle"))
        self.lbl_section.configure(text=self.i18n.t(title_key))
        self.lbl_section_sub.configure(text=self.i18n.t(subtitle_key))

        # Show one
        self.views[name].grid(row=0, column=0, sticky="nsew")

    def log_message(self, msg):
        self.views["logs"].append(msg)
    
    def on_scan_complete(self, playlists):
        self.views["vk"].update_playlists(playlists)
        self.on_log_message(self.i18n.t("app.playlists.received"))
        self._schedule_after(100, lambda: self.show_view("vk"))

    def on_progress(self, val):
        pass # Optional: Add progress bar to sidebar if requested.

    def on_download_complete(self):
        self.log_message(self.i18n.t("app.download.complete"))
        
    def on_login_success(self):
        self.log_message(self.i18n.t("app.login.success"))
        self.views["vk"].set_connected_status(True)
    
    def on_log_message(self, msg):
        # Compatibility wrapper
        self.log_message(msg)

    def get_strategy_from_ui(self):
        return self.views["tg"].get_strategy()

    def on_language_change(self, value):
        language = "ru" if value == "RU" else "en"
        if language == self.i18n.language:
            return
        self.i18n.set_language(language)
        if hasattr(self.controller, "set_language"):
            self.controller.set_language(language)

    def apply_language(self):
        self.title(self.i18n.t("app.title"))
        self.lbl_logo.configure(text=self.i18n.t("app.logo"))
        self.lbl_logo_sub.configure(text=self.i18n.t("app.logo.subtitle"))
        self.lbl_lang.configure(text=self.i18n.t("app.lang"))
        self.lbl_ver.configure(text=self.i18n.t("app.version"))

        self.btn_dash.configure(text=self.i18n.t("nav.dashboard"))
        self.btn_vk.configure(text=self.i18n.t("nav.downloader"))
        self.btn_tg.configure(text=self.i18n.t("nav.telegram"))
        self.btn_logs.configure(text=self.i18n.t("nav.logs"))

        title_key, subtitle_key = self.view_titles.get(self.current_view, ("dashboard.title", "dashboard.subtitle"))
        self.lbl_section.configure(text=self.i18n.t(title_key))
        self.lbl_section_sub.configure(text=self.i18n.t(subtitle_key))

        for view in self.views.values():
            if hasattr(view, "apply_language"):
                view.apply_language()

    def update_stats_loop(self):
        if self._is_closing or not self._window_alive():
            return

        # Update dashboard every 5s
        if self.views.get("dashboard"):
            try:
                self.views["dashboard"].update_stats()
            except Exception:
                pass
        self._schedule_after(5000, self.update_stats_loop)

    def on_close(self):
        self._is_closing = True
        self._cancel_after_callbacks()
        try:
            self.controller.close_app()
        except Exception:
            pass
        if self._window_alive():
            self.destroy()

    def process_ui_events(self):
        if self._is_closing or not self._window_alive():
            return

        try:
            while True:
                event, payload = self._ui_events.get_nowait()
                if event == "log":
                    self.log_message(payload)
                elif event == "scan_complete":
                    self.on_scan_complete(payload)
                elif event == "progress":
                    self.on_progress(payload)
                elif event == "download_complete":
                    self.on_download_complete()
                elif event == "login_success":
                    self.on_login_success()
        except Empty:
            pass

        self._schedule_after(120, self.process_ui_events)
