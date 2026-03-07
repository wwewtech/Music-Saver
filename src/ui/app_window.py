import customtkinter as ctk
from tkinter import TclError
from queue import Queue, Empty
from src.ui.views.dashboard_view import DashboardView
from src.ui.views.downloader_view import DownloaderView
from src.ui.views.telegram_view import TelegramView
from src.ui.views.logs_view import LogsView
from src.ui.i18n import I18n
from src.ui.design_system import get_theme, ui_font, button_style


class AppWindow(ctk.CTk):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.theme = get_theme()

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
        self.controller.on_preferred_source_changed = lambda source: self._ui_events.put(("preferred_source_changed", source))
        
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
            font=ui_font(self.theme, 22, "bold"),
            text_color=self.theme["text"],
            anchor="w",
        )
        self.lbl_logo.pack(fill="x")

        self.lbl_logo_sub = ctk.CTkLabel(
            brand_frame,
            text=self.i18n.t("app.logo.subtitle"),
            font=ui_font(self.theme, 12, alt=True),
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
            font=ui_font(self.theme, 12, "bold", alt=True),
            text_color=self.theme["muted"],
            anchor="w",
        )
        self.lbl_lang.pack(fill="x", padx=12, pady=(12, 2))

        self.lang_switch = ctk.CTkFrame(nav_block, fg_color=self.theme["surface"], corner_radius=10)
        self.lang_switch.pack(fill="x", padx=12, pady=(4, 12))

        self.btn_lang_ru = ctk.CTkButton(
            self.lang_switch,
            text="RU",
            command=lambda: self.on_language_change("RU"),
            corner_radius=8,
            height=32,
            font=ui_font(self.theme, 12, "bold"),
        )
        self.btn_lang_ru.pack(side="left", fill="x", expand=True, padx=(4, 2), pady=4)

        self.btn_lang_en = ctk.CTkButton(
            self.lang_switch,
            text="EN",
            command=lambda: self.on_language_change("EN"),
            corner_radius=8,
            height=32,
            font=ui_font(self.theme, 12, "bold"),
        )
        self.btn_lang_en.pack(side="left", fill="x", expand=True, padx=(2, 4), pady=4)
        self._set_language_buttons("ru" if self.i18n.language == "ru" else "en")
        
        self.btn_dash = self.create_nav_btn(nav_block, self.i18n.t("nav.dashboard"), "dashboard")
        self.btn_vk = self.create_nav_btn(nav_block, self.i18n.t("nav.downloader"), "vk")
        self.btn_tg = self.create_nav_btn(nav_block, self.i18n.t("nav.telegram"), "tg")
        self.btn_logs = self.create_nav_btn(nav_block, self.i18n.t("nav.logs"), "logs")
        
        # Small footer
        self.lbl_ver = ctk.CTkLabel(
            self.sidebar,
            text=self.i18n.t("app.version"),
            text_color=self.theme["muted"],
            font=ui_font(self.theme, 11, alt=True),
        )
        self.lbl_ver.pack(side="bottom", pady=14)

    def create_nav_btn(self, parent, text, view_name):
        nav_style = button_style(self.theme, "nav")
        btn = ctk.CTkButton(
            parent,
            text=text,
            fg_color=nav_style["fg_color"],
            text_color=nav_style["text_color"],
            hover_color=nav_style["hover_color"],
            anchor="w",
            corner_radius=12,
            border_spacing=14,
            height=46,
            font=ui_font(self.theme, 14, "bold", alt=True),
            command=lambda: self.show_view(view_name),
        )
        btn.pack(fill="x", padx=10, pady=4)
        return btn

    def _set_language_buttons(self, language):
        active_style = button_style(self.theme, "primary")
        idle_style = button_style(self.theme, "secondary")
        if language == "ru":
            self.btn_lang_ru.configure(**active_style)
            self.btn_lang_en.configure(**idle_style)
        else:
            self.btn_lang_ru.configure(**idle_style)
            self.btn_lang_en.configure(**active_style)

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
            font=ui_font(self.theme, 24, "bold"),
            text_color=self.theme["text"],
            anchor="w",
        )
        self.lbl_section.grid(row=0, column=0, sticky="w", padx=18, pady=(14, 0))

        self.lbl_section_sub = ctk.CTkLabel(
            self.topbar,
            text="",
            font=ui_font(self.theme, 12, alt=True),
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
            btn.configure(**button_style(self.theme, "nav"))
            
        # Highlight active
        btn_map = {
            "dashboard": self.btn_dash,
            "vk": self.btn_vk,
            "tg": self.btn_tg,
            "logs": self.btn_logs
        }
        if name in btn_map:
            btn_map[name].configure(**button_style(self.theme, "nav_active"))

        title_key, subtitle_key = self.view_titles.get(name, ("dashboard.title", "dashboard.subtitle"))
        self.lbl_section.configure(text=self.i18n.t(title_key))
        self.lbl_section_sub.configure(text=self.i18n.t(subtitle_key))

        # Show one
        target_view = self.views[name]
        if hasattr(target_view, "on_show"):
            target_view.on_show()
        target_view.grid(row=0, column=0, sticky="nsew")

    def log_message(self, msg):
        self.views["logs"].append(msg)
    
    def on_scan_complete(self, playlists):
        self.views["vk"].update_playlists(playlists)
        if "tg" in self.views and hasattr(self.views["tg"], "set_yandex_collection_status"):
            has_yandex = any(str(getattr(pl, "id", "")).startswith("ym:") for pl in playlists or [])
            self.views["tg"].set_yandex_collection_status(has_yandex)
        self.on_log_message(self.i18n.t("app.playlists.received"))
        self._schedule_after(100, lambda: self.show_view("vk"))

    def on_progress(self, val):
        pass # Optional: Add progress bar to sidebar if requested.

    def on_download_complete(self):
        self.log_message(self.i18n.t("app.download.complete"))
        
    def on_login_success(self):
        self.log_message(self.i18n.t("app.login.success"))
        self.views["vk"].set_connected_status(True)
        if "tg" in self.views and hasattr(self.views["tg"], "set_vk_connected_status"):
            self.views["tg"].set_vk_connected_status(True)
    
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
        self._set_language_buttons(language)
        if hasattr(self.controller, "set_language"):
            self.controller.set_language(language)

    def apply_language(self):
        self.title(self.i18n.t("app.title"))
        self._set_language_buttons(self.i18n.language)
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
                elif event == "preferred_source_changed":
                    if "vk" in self.views and hasattr(self.views["vk"], "set_source"):
                        self.views["vk"].set_source(payload)
        except Empty:
            pass

        self._schedule_after(120, self.process_ui_events)
