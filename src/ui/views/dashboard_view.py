import os
import tkinter as tk

import customtkinter as ctk

from src.ui.components.primitives import EmptyState, MetricTile, SectionHeader, StatusBadge, Surface, set_resize_lock, flush_pending_wraps
from src.ui.design_system import button_style, ui_font


class DashboardView(ctk.CTkFrame):
    def __init__(self, master, controller, i18n, theme):
        super().__init__(master, fg_color="transparent")
        self.controller = controller
        self.i18n = i18n
        self.theme = theme
        self.cards = {}
        self._last_stats = None
        self.setup_ui()

    def setup_ui(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.container = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            corner_radius=0,
        )
        self.container.grid(row=0, column=0, sticky="nsew")
        self.container.grid_columnconfigure(0, weight=3)
        self.container.grid_columnconfigure(1, weight=2)
        self.container.grid_rowconfigure(1, weight=0)
        self.container.grid_rowconfigure(2, weight=1)

        self.hero_card = MetricTile(
            self.container,
            self.theme,
            self.i18n.t("dashboard.hero.title"),
            "0",
            accent=True,
            description=self.i18n.t("dashboard.hero.subtitle"),
        )
        self.hero_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=(0, 8))

        self.readiness_card = Surface(self.container, self.theme, variant="panel")
        self.readiness_card.grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=(0, 8))

        self.readiness_header = SectionHeader(
            self.readiness_card,
            self.theme,
            self.i18n.t("dashboard.readiness.title"),
            self.i18n.t("dashboard.readiness.subtitle"),
        )
        self.readiness_header.pack(fill="x", padx=18, pady=(16, 14))

        self.badge_rows = {}
        for key in ("source", "telegram", "storage"):
            row = tk.Frame(self.readiness_card, bg=self.theme["panel"])
            row.pack(fill="x", padx=18, pady=5)
            label = ctk.CTkLabel(
                row,
                text=self.i18n.t(f"dashboard.readiness.{key}"),
                font=ui_font(self.theme, 12, "bold", alt=True),
                text_color=self.theme["text_soft"],
                anchor="w",
            )
            label.pack(side="left")
            badge = StatusBadge(row, self.theme, self.i18n.t("dashboard.readiness.pending"))
            badge.pack(side="right")
            self.badge_rows[key] = (label, badge)

        self.metrics_row = tk.Frame(self.container, bg=self.theme["page_bg"])
        self.metrics_row.grid(row=1, column=0, columnspan=2, sticky="ew", pady=8)
        for column in range(3):
            self.metrics_row.grid_columnconfigure(column, weight=1)

        self.card_downloaded = MetricTile(
            self.metrics_row,
            self.theme,
            self.i18n.t("dashboard.downloaded"),
            "0",
        )
        self.card_downloaded.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        self.card_uploaded = MetricTile(
            self.metrics_row,
            self.theme,
            self.i18n.t("dashboard.uploaded"),
            "0",
        )
        self.card_uploaded.grid(row=0, column=1, sticky="ew", padx=8)

        self.card_storage = MetricTile(
            self.metrics_row,
            self.theme,
            self.i18n.t("dashboard.storage"),
            "0 MB",
        )
        self.card_storage.grid(row=0, column=2, sticky="ew", padx=(8, 0))

        self.activity_card = Surface(self.container, self.theme, variant="surface")
        self.activity_card.grid(row=2, column=0, sticky="nsew", padx=(0, 8), pady=(8, 0))

        self.activity_header = SectionHeader(
            self.activity_card,
            self.theme,
            self.i18n.t("dashboard.activity.title"),
            self.i18n.t("dashboard.activity.subtitle"),
        )
        self.activity_header.pack(fill="x", padx=18, pady=(16, 12))

        self.activity_body = EmptyState(
            self.activity_card,
            self.theme,
            self.i18n.t("dashboard.activity.empty.title"),
            self.i18n.t("dashboard.activity.empty.body"),
        )
        self.activity_body.pack(fill="x", padx=18, pady=(0, 18))

        self.actions_card = Surface(self.container, self.theme, variant="surface")
        self.actions_card.grid(row=2, column=1, sticky="nsew", padx=(8, 0), pady=(8, 0))

        self.actions_header = SectionHeader(
            self.actions_card,
            self.theme,
            self.i18n.t("dashboard.actions.title"),
            self.i18n.t("dashboard.actions.subtitle"),
        )
        self.actions_header.pack(fill="x", padx=18, pady=(16, 10))

        self.action_buttons = []
        action_specs = [
            ("dashboard.actions.downloads", lambda: self.winfo_toplevel().show_view("vk")),
            ("dashboard.actions.settings", lambda: self.winfo_toplevel().show_view("tg")),
            ("dashboard.actions.logs", lambda: self.winfo_toplevel().show_view("logs")),
        ]
        for key, command in action_specs:
            tile = Surface(self.actions_card, self.theme, variant="soft")
            tile.pack(fill="x", padx=18, pady=6)

            title = ctk.CTkLabel(
                tile,
                text=self.i18n.t(f"{key}.title"),
                font=ui_font(self.theme, 13, "bold"),
                text_color=self.theme["text"],
                anchor="w",
            )
            title.pack(fill="x", padx=14, pady=(12, 2))

            body = ctk.CTkLabel(
                tile,
                text=self.i18n.t(f"{key}.body"),
                font=ui_font(self.theme, 12, alt=True),
                text_color=self.theme["muted"],
                justify="left",
                anchor="w",
                wraplength=280,
            )
            body.pack(fill="x", padx=14, pady=(0, 8))

            button = ctk.CTkButton(
                tile,
                text=self.i18n.t(f"{key}.cta"),
                height=36,
                corner_radius=10,
                font=ui_font(self.theme, 12, "bold"),
                command=command,
                **button_style(self.theme, "secondary"),
            )
            button.pack(anchor="w", padx=14, pady=(0, 12))
            self.action_buttons.append((key, title, body, button))

    def apply_language(self):
        set_resize_lock(True)
        self.hero_card.set_label(self.i18n.t("dashboard.hero.title"))
        self.hero_card.set_description(self.i18n.t("dashboard.hero.subtitle"))
        self.readiness_header.configure_content(
            title=self.i18n.t("dashboard.readiness.title"),
            description=self.i18n.t("dashboard.readiness.subtitle"),
        )
        for key, (label, _badge) in self.badge_rows.items():
            label.configure(text=self.i18n.t(f"dashboard.readiness.{key}"))
        self.card_downloaded.set_label(self.i18n.t("dashboard.downloaded"))
        self.card_uploaded.set_label(self.i18n.t("dashboard.uploaded"))
        self.card_storage.set_label(self.i18n.t("dashboard.storage"))
        self.activity_header.configure_content(
            title=self.i18n.t("dashboard.activity.title"),
            description=self.i18n.t("dashboard.activity.subtitle"),
        )
        self.activity_body.configure_content(
            self.i18n.t("dashboard.activity.empty.title"),
            self.i18n.t("dashboard.activity.empty.body"),
        )
        self.actions_header.configure_content(
            title=self.i18n.t("dashboard.actions.title"),
            description=self.i18n.t("dashboard.actions.subtitle"),
        )
        for key, title, body, button in self.action_buttons:
            title.configure(text=self.i18n.t(f"{key}.title"))
            body.configure(text=self.i18n.t(f"{key}.body"))
            button.configure(text=self.i18n.t(f"{key}.cta"))
        set_resize_lock(False)
        flush_pending_wraps()
        if self._last_stats is not None:
            self.apply_stats(self._last_stats, force=True)

    def update_stats(self):
        stats = self.controller.get_dashboard_stats()
        self.apply_stats(stats)

    def apply_stats(self, stats, force=False):
        if stats == self._last_stats and not force:
            return

        playlists = stats.get("playlists", 0)
        tracks_total = stats.get("tracks_total", 0)
        downloaded = stats.get("tracks_downloaded", 0)
        uploaded = stats.get("tracks_uploaded", 0)
        storage_mb = stats.get("storage_mb", 0)

        self.hero_card.set_value(str(playlists))
        self.hero_card.set_description(
            self.i18n.t("dashboard.hero.detail", tracks=tracks_total)
        )
        self.card_downloaded.set_value(str(downloaded))
        self.card_uploaded.set_value(str(uploaded))
        self.card_storage.set_value(f"{storage_mb} MB")

        tg_ready = self.controller.is_telegram_configured()
        strategy = self.controller.get_processing_strategy()
        storage_ready = os.path.exists(self.controller.get_download_dir())

        source_tone = "success" if playlists else "warning"
        source_text = (
            self.i18n.t("dashboard.readiness.ready")
            if playlists
            else self.i18n.t("dashboard.readiness.pending")
        )
        telegram_tone = (
            "info"
            if strategy == "download_only" and not tg_ready
            else "success"
            if tg_ready
            else "warning"
        )
        telegram_text = (
            self.i18n.t("dashboard.readiness.local")
            if strategy == "download_only" and not tg_ready
            else self.i18n.t("dashboard.readiness.ready")
            if tg_ready
            else self.i18n.t("dashboard.readiness.pending")
        )
        storage_tone = "success" if storage_ready else "warning"
        storage_text = (
            self.i18n.t("dashboard.readiness.ready")
            if storage_ready
            else self.i18n.t("dashboard.readiness.pending")
        )

        self.badge_rows["source"][1].configure_tone(source_tone, source_text)
        self.badge_rows["telegram"][1].configure_tone(telegram_tone, telegram_text)
        self.badge_rows["storage"][1].configure_tone(storage_tone, storage_text)

        if downloaded or uploaded:
            self.activity_body.configure_content(
                self.i18n.t("dashboard.activity.live.title"),
                self.i18n.t(
                    "dashboard.activity.live.body",
                    downloaded=downloaded,
                    uploaded=uploaded,
                ),
            )
        else:
            self.activity_body.configure_content(
                self.i18n.t("dashboard.activity.empty.title"),
                self.i18n.t("dashboard.activity.empty.body"),
            )

        self._last_stats = dict(stats)
