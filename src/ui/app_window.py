import customtkinter as ctk
import tkinter as tk
from tkinter import TclError
from queue import Queue, Empty
from concurrent.futures import ThreadPoolExecutor
import os
from src.app_config import RESOURCE_DIR
from src.ui.components.primitives import SectionHeader, StatusBadge, Surface, set_resize_lock, flush_pending_wraps
from src.ui.views.dashboard_view import DashboardView
from src.ui.views.downloader_view import DownloaderView
from src.ui.views.telegram_view import TelegramView
from src.ui.views.logs_view import LogsView
from src.ui.i18n import I18n
from src.ui.design_system import get_theme, ui_font, button_style


class AppWindow(ctk.CTk):
    STATS_POLL_INTERVAL_MS = 30000
    UI_EVENTS_POLL_MS = 250
    MAX_UI_EVENTS_PER_TICK = 50
    RESIZE_SETTLE_MS = 250
    PENDING_LOGS_MAX = 2000
    DEFAULT_WIDTH = 1320
    DEFAULT_HEIGHT = 880
    MIN_WIDTH = 980
    MIN_HEIGHT = 680

    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.theme = get_theme()

        lang = (
            self.controller.get_language()
            if hasattr(self.controller, "get_language")
            else "ru"
        )
        self.i18n = I18n(lang)
        self.i18n.subscribe(self.apply_language)
        self._ui_events = Queue()
        self._after_ids = set()
        self._is_closing = False
        self._stats_fetch_in_progress = False
        self._stats_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="ui-stats")
        self._pending_logs = []
        self._resize_restore_id = None
        self._last_window_size = None
        self._views_language_state = {}
        self.current_view = None
        self._active_nav_btn = None
        self._nav_style = button_style(self.theme, "nav")
        self._nav_active_style = button_style(self.theme, "nav_active")
        self.view_titles = {
            "dashboard": ("dashboard.title", "dashboard.subtitle"),
            "vk": ("downloader.title", "downloader.subtitle"),
            "tg": ("telegram.title", "telegram.subtitle"),
            "logs": ("logs.title", "logs.subtitle"),
        }

        self.title(self.i18n.t("app.title"))
        self.configure(fg_color=self.theme["page_bg"])
        self._configure_window_geometry()

        # Установка иконки приложения
        icon_path = os.path.join(RESOURCE_DIR, "resources", "MusicSaver.ico")
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception as e:
                print(f"Failed to set icon: {e}")

        # Configure Controller Callbacks
        self.controller.on_log = lambda msg: self._ui_events.put(("log", msg))
        self.controller.on_scan_complete = lambda playlists: self._ui_events.put(
            ("scan_complete", playlists)
        )
        self.controller.on_progress = lambda val: self._ui_events.put(("progress", val))
        self.controller.on_download_complete = lambda: self._ui_events.put(
            ("download_complete", None)
        )
        self.controller.on_login_success = lambda: self._ui_events.put(
            ("login_success", None)
        )
        self.controller.on_preferred_source_changed = (
            lambda source: self._ui_events.put(("preferred_source_changed", source))
        )

        # Hook for strategy
        self.controller.get_current_strategy = self.get_strategy_from_ui

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.setup_sidebar()
        self.setup_views()
        self.bind("<Configure>", self._on_window_configure)

        # Start Clock/Stats Loop
        self.update_stats_loop()
        self.process_ui_events()

    def _configure_window_geometry(self):
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        available_width = max(self.MIN_WIDTH, screen_width - 80)
        available_height = max(self.MIN_HEIGHT, screen_height - 100)

        min_width = min(self.MIN_WIDTH, available_width)
        min_height = min(self.MIN_HEIGHT, available_height)
        width = min(self.DEFAULT_WIDTH, available_width)
        height = min(self.DEFAULT_HEIGHT, available_height)

        self.minsize(min_width, min_height)

        pos_x = max((screen_width - width) // 2, 0)
        pos_y = max((screen_height - height) // 2 - 20, 0)
        self.geometry(f"{width}x{height}+{pos_x}+{pos_y}")

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
        self.sidebar = Surface(
            self,
            self.theme,
            variant="panel",
            width=280,
            corner_radius=0,
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        brand_frame = tk.Frame(self.sidebar, bg=self.theme["panel"])
        brand_frame.pack(fill="x", padx=20, pady=(24, 14))

        self.lbl_shell_caption = ctk.CTkLabel(
            brand_frame,
            text=self.i18n.t("app.header.caption"),
            font=ui_font(self.theme, 11, "bold", alt=True),
            text_color=self.theme["muted"],
            anchor="w",
        )
        self.lbl_shell_caption.pack(fill="x", pady=(0, 6))

        self.lbl_logo = ctk.CTkLabel(
            brand_frame,
            text=self.i18n.t("app.logo"),
            font=ui_font(self.theme, 24, "bold"),
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
        self.lbl_logo_sub.pack(fill="x", pady=(4, 0))

        nav_block = tk.Frame(self.sidebar, bg=self.theme["panel"])
        nav_block.pack(fill="x", padx=14, pady=(6, 0))

        self.lbl_nav = ctk.CTkLabel(
            nav_block,
            text=self.i18n.t("app.sidebar.nav"),
            font=ui_font(self.theme, 11, "bold", alt=True),
            text_color=self.theme["muted"],
            anchor="w",
        )
        self.lbl_nav.pack(fill="x", padx=8, pady=(0, 8))

        self.nav_surface = Surface(nav_block, self.theme, variant="soft")
        self.nav_surface.pack(fill="x")

        self.lbl_lang = ctk.CTkLabel(
            self.nav_surface,
            text=self.i18n.t("app.lang"),
            font=ui_font(self.theme, 12, "bold", alt=True),
            text_color=self.theme["muted"],
            anchor="w",
        )
        self.lbl_lang.pack(fill="x", padx=14, pady=(14, 4))

        self.lang_switch = ctk.CTkFrame(
            self.nav_surface, fg_color=self.theme["surface_emphasis"], corner_radius=12
        )
        self.lang_switch.pack(fill="x", padx=14, pady=(0, 14))

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

        self.btn_dash = self.create_nav_btn(
            self.nav_surface, self.i18n.t("nav.dashboard"), "dashboard"
        )
        self.btn_vk = self.create_nav_btn(
            self.nav_surface, self.i18n.t("nav.downloader"), "vk"
        )
        self.btn_tg = self.create_nav_btn(
            self.nav_surface, self.i18n.t("nav.telegram"), "tg"
        )
        self.btn_logs = self.create_nav_btn(
            self.nav_surface, self.i18n.t("nav.logs"), "logs"
        )

        self.side_note = Surface(self.sidebar, self.theme, variant="soft")
        self.side_note.pack(side="bottom", fill="x", padx=14, pady=14)

        self.lbl_note_title = ctk.CTkLabel(
            self.side_note,
            text=self.i18n.t("app.sidebar.note.title"),
            text_color=self.theme["text_soft"],
            font=ui_font(self.theme, 12, "bold", alt=True),
            anchor="w",
        )
        self.lbl_note_title.pack(fill="x", padx=14, pady=(14, 4))

        self.lbl_note_body = ctk.CTkLabel(
            self.side_note,
            text=self.i18n.t("app.sidebar.note.body"),
            text_color=self.theme["muted"],
            font=ui_font(self.theme, 12, alt=True),
            justify="left",
            anchor="w",
            wraplength=220,
        )
        self.lbl_note_body.pack(fill="x", padx=14, pady=(0, 10))

        self.lbl_ver = ctk.CTkLabel(
            self.side_note,
            text=self.i18n.t("app.version"),
            text_color=self.theme["muted_soft"],
            font=ui_font(self.theme, 11, alt=True),
            anchor="w",
        )
        self.lbl_ver.pack(fill="x", padx=14, pady=(0, 14))

    def create_nav_btn(self, parent, text, view_name):
        nav_style = button_style(self.theme, "nav")
        btn = ctk.CTkButton(
            parent,
            text=text,
            fg_color=nav_style["fg_color"],
            text_color=nav_style["text_color"],
            hover_color=nav_style["hover_color"],
            anchor="w",
            corner_radius=14,
            border_spacing=16,
            height=50,
            font=ui_font(self.theme, 14, "bold", alt=True),
            command=lambda: self.show_view(view_name),
            border_width=nav_style["border_width"],
            border_color=nav_style["border_color"],
        )
        btn.pack(fill="x", padx=14, pady=5)
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
        self.main_area = tk.Frame(self, bg=self.theme["page_bg"])
        self.main_area.grid(row=0, column=1, sticky="nsew", padx=16, pady=16)
        self.main_area.grid_rowconfigure(1, weight=1)
        self.main_area.grid_columnconfigure(0, weight=1)

        self.topbar = Surface(self.main_area, self.theme, variant="panel", height=106)
        self.topbar.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        self.topbar.grid_columnconfigure(0, weight=1)
        self.topbar.grid_columnconfigure(1, weight=0)

        self.topbar_header = SectionHeader(
            self.topbar,
            self.theme,
            "",
            "",
            eyebrow=self.i18n.t("app.header.caption"),
        )
        self.topbar_header.grid(row=0, column=0, sticky="w", padx=18, pady=16)
        self.lbl_section = self.topbar_header.title
        self.lbl_section_sub = self.topbar_header.description

        self.live_badge = StatusBadge(
            self.topbar,
            self.theme,
            self.i18n.t("app.topbar.live"),
            tone="info",
        )
        self.live_badge.grid(row=0, column=1, sticky="e", padx=18, pady=18)

        self.view_container = tk.Frame(self.main_area, bg=self.theme["page_bg"])
        self.view_container.grid(row=1, column=0, sticky="nsew")
        self.view_container.grid_rowconfigure(0, weight=1)
        self.view_container.grid_columnconfigure(0, weight=1)
        self.view_container.grid_propagate(False)

        self.views = {}
        self._view_constructors = {
            "dashboard": lambda: DashboardView(
                self.view_container, self.controller, self.i18n, self.theme
            ),
            "vk": lambda: DownloaderView(
                self.view_container, self.controller, self.i18n, self.theme
            ),
            "tg": lambda: TelegramView(
                self.view_container, self.controller, self.i18n, self.theme
            ),
            "logs": lambda: LogsView(self.view_container, self.i18n, self.theme),
        }

        # Init default
        self.show_view("dashboard")

    def _get_or_create_view(self, name):
        if name not in self.views:
            constructor = self._view_constructors.get(name)
            if constructor is None:
                return None
            view = constructor()
            self.views[name] = view
            self._views_language_state[name] = self.i18n.language
        return self.views[name]

    def show_view(self, name):
        if name not in self._view_constructors:
            return

        if self.current_view == name:
            return

        previous_view = self.current_view
        self.current_view = name

        btn_map = {
            "dashboard": self.btn_dash,
            "vk": self.btn_vk,
            "tg": self.btn_tg,
            "logs": self.btn_logs,
        }

        if previous_view and previous_view in btn_map:
            btn_map[previous_view].configure(**self._nav_style)
        if name in btn_map:
            btn_map[name].configure(**self._nav_active_style)

        title_key, subtitle_key = self.view_titles.get(
            name, ("dashboard.title", "dashboard.subtitle")
        )
        self.lbl_section.configure(text=self.i18n.t(title_key))
        self.lbl_section_sub.configure(text=self.i18n.t(subtitle_key))

        # Hide previous view entirely from geometry manager
        if previous_view and previous_view in self.views:
            self.views[previous_view].grid_forget()

        # Create or get target view, and grid it
        target_view = self._get_or_create_view(name)
        if target_view is None:
            return
        self._ensure_view_language(name)
        target_view.grid(row=0, column=0, sticky="nsew")
        if hasattr(target_view, "on_show"):
            target_view.on_show()

        if name == "logs":
            self._flush_pending_logs()

        if name == "dashboard" and self.views.get("dashboard"):
            self._request_dashboard_stats_async()

    def _request_dashboard_stats_async(self):
        if (
            self._is_closing
            or not self._window_alive()
            or self.current_view != "dashboard"
            or self._stats_fetch_in_progress
        ):
            return

        self._stats_fetch_in_progress = True

        def _worker():
            try:
                stats = self.controller.get_dashboard_stats()
                self._ui_events.put(("dashboard_stats", stats))
            except Exception as exc:
                self._ui_events.put(("log", f"Ошибка обновления статистики: {exc}"))
            finally:
                self._ui_events.put(("dashboard_stats_done", None))

        self._stats_executor.submit(_worker)

    def log_message(self, msg):
        if self.current_view == "logs":
            self.views["logs"].append(msg)
            return

        self._pending_logs.append(msg)
        if len(self._pending_logs) > self.PENDING_LOGS_MAX:
            self._pending_logs = self._pending_logs[-self.PENDING_LOGS_MAX :]

    def _flush_pending_logs(self):
        if not self._pending_logs:
            return
        self.views["logs"].append_many(self._pending_logs)
        self._pending_logs.clear()

    def _on_window_configure(self, event):
        if event.widget is not self:
            return

        w = self.winfo_width()
        h = self.winfo_height()
        window_size = (w, h)
        if window_size == self._last_window_size:
            return

        self._last_window_size = window_size
        set_resize_lock(True)

        if self._resize_restore_id is not None:
            try:
                self.after_cancel(self._resize_restore_id)
            except TclError:
                pass
            self._resize_restore_id = None

        self._resize_restore_id = self._schedule_after(
            self.RESIZE_SETTLE_MS, self._finish_window_resize
        )

    def _finish_window_resize(self):
        self._resize_restore_id = None
        set_resize_lock(False)
        flush_pending_wraps()

    def _ensure_view_language(self, name, force=False):
        if name not in self.views:
            return

        if not force and self._views_language_state.get(name) == self.i18n.language:
            return

        view = self.views[name]
        if hasattr(view, "apply_language"):
            view.apply_language()
        self._views_language_state[name] = self.i18n.language

    def on_scan_complete(self, playlists):
        if "vk" in self.views:
            self.views["vk"].update_playlists(playlists)
        if "tg" in self.views and hasattr(
            self.views["tg"], "set_yandex_collection_status"
        ):
            has_yandex = any(
                str(getattr(pl, "id", "")).startswith("ym:") for pl in playlists or []
            )
            self.views["tg"].set_yandex_collection_status(has_yandex)
        self.on_log_message(self.i18n.t("app.playlists.received"))
        self._schedule_after(100, lambda: self.show_view("vk"))

    def on_progress(self, val):
        pass  # Optional: Add progress bar to sidebar if requested.

    def on_download_complete(self):
        self.log_message(self.i18n.t("app.download.complete"))

    def on_login_success(self):
        self.log_message(self.i18n.t("app.login.success"))
        if "vk" in self.views:
            self.views["vk"].set_connected_status(True)
        if "tg" in self.views and hasattr(self.views["tg"], "set_vk_connected_status"):
            self.views["tg"].set_vk_connected_status(True)

    def on_log_message(self, msg):
        # Compatibility wrapper
        self.log_message(msg)

    def get_strategy_from_ui(self):
        tg_view = self._get_or_create_view("tg")
        return tg_view.get_strategy()

    def on_language_change(self, value):
        language = "ru" if value == "RU" else "en"
        if language == self.i18n.language:
            return
        self.i18n.set_language(language)
        self._set_language_buttons(language)
        if hasattr(self.controller, "set_language"):
            self.controller.set_language(language)

    def apply_language(self):
        set_resize_lock(True)

        self.title(self.i18n.t("app.title"))
        self._set_language_buttons(self.i18n.language)
        self.lbl_logo.configure(text=self.i18n.t("app.logo"))
        self.lbl_logo_sub.configure(text=self.i18n.t("app.logo.subtitle"))
        self.lbl_shell_caption.configure(text=self.i18n.t("app.header.caption"))
        self.lbl_nav.configure(text=self.i18n.t("app.sidebar.nav"))
        self.lbl_lang.configure(text=self.i18n.t("app.lang"))
        self.lbl_ver.configure(text=self.i18n.t("app.version"))
        self.lbl_note_title.configure(text=self.i18n.t("app.sidebar.note.title"))
        self.lbl_note_body.configure(text=self.i18n.t("app.sidebar.note.body"))
        self.topbar_header.configure_content(eyebrow=self.i18n.t("app.header.caption"))
        self.live_badge.configure_tone("info", self.i18n.t("app.topbar.live"))

        self.btn_dash.configure(text=self.i18n.t("nav.dashboard"))
        self.btn_vk.configure(text=self.i18n.t("nav.downloader"))
        self.btn_tg.configure(text=self.i18n.t("nav.telegram"))
        self.btn_logs.configure(text=self.i18n.t("nav.logs"))

        title_key, subtitle_key = self.view_titles.get(
            self.current_view, ("dashboard.title", "dashboard.subtitle")
        )
        self.lbl_section.configure(text=self.i18n.t(title_key))
        self.lbl_section_sub.configure(text=self.i18n.t(subtitle_key))

        for view_name in self.views:
            self._views_language_state[view_name] = None
        # Also mark uncreated views as needing language update
        for view_name in self._view_constructors:
            if view_name not in self.views:
                self._views_language_state[view_name] = None

        if self.current_view is not None:
            self._ensure_view_language(self.current_view, force=True)

        set_resize_lock(False)
        flush_pending_wraps()

    def update_stats_loop(self):
        if self._is_closing or not self._window_alive():
            return

        # Update dashboard only when visible to keep UI responsive
        if self.current_view == "dashboard" and self.views.get("dashboard"):
            self._request_dashboard_stats_async()
        self._schedule_after(self.STATS_POLL_INTERVAL_MS, self.update_stats_loop)

    def on_close(self):
        self._is_closing = True
        set_resize_lock(False)
        self._cancel_after_callbacks()
        try:
            self._stats_executor.shutdown(wait=False, cancel_futures=True)
        except Exception:
            pass
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
            processed = 0
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
                elif event == "dashboard_stats":
                    if "dashboard" in self.views and hasattr(
                        self.views["dashboard"], "apply_stats"
                    ):
                        self.views["dashboard"].apply_stats(payload)
                elif event == "dashboard_stats_done":
                    self._stats_fetch_in_progress = False

                processed += 1
                if processed >= self.MAX_UI_EVENTS_PER_TICK:
                    break
        except Empty:
            pass

        self._schedule_after(self.UI_EVENTS_POLL_MS, self.process_ui_events)
