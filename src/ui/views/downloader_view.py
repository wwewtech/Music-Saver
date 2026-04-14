import tkinter as tk
import customtkinter as ctk
from src.ui.components.primitives import (
    SectionHeader,
    Surface,
    bind_auto_wrap,
    set_resize_lock,
    flush_pending_wraps,
)
from src.ui.design_system import button_style, checkbox_style, ui_font


class DownloaderView(ctk.CTkFrame):
    def __init__(self, master, controller, i18n, theme):
        super().__init__(master, fg_color="transparent")
        self.controller = controller
        self.i18n = i18n
        self.theme = theme
        self.is_connected = False
        self.checkboxes = []
        self.current_source = "vk"
        self.all_playlists = []
        self.setup_ui()
        self.apply_preferred_source()

    def setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        source_frame = Surface(self, self.theme, variant="surface")
        source_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        source_frame.grid_columnconfigure(0, weight=0)
        source_frame.grid_columnconfigure(1, weight=1)
        source_frame.grid_columnconfigure(2, weight=0)

        self.lbl_source = ctk.CTkLabel(
            source_frame,
            text=self.i18n.t("downloader.source"),
            font=ui_font(self.theme, 12, "bold", alt=True),
            text_color=self.theme["muted"],
            anchor="w",
        )
        self.lbl_source.grid(row=0, column=0, sticky="w", padx=(14, 10), pady=14)

        self.source_selector = ctk.CTkSegmentedButton(
            source_frame,
            values=[
                self.i18n.t("downloader.source.vk"),
                self.i18n.t("downloader.source.yandex"),
            ],
            command=self._on_source_changed,
            height=34,
            font=ui_font(self.theme, 12, "bold"),
        )
        self.source_selector.grid(row=0, column=1, sticky="ew", pady=10)
        self.source_selector.set(self.i18n.t("downloader.source.vk"))

        self.lbl_status = ctk.CTkLabel(
            source_frame,
            text=self.i18n.t("downloader.status.idle"),
            text_color=self.theme["muted"],
            font=ui_font(self.theme, 12, "bold", alt=True),
            anchor="w",
            justify="left",
        )
        self.lbl_status.grid(
            row=1, column=0, columnspan=3, sticky="ew", padx=14, pady=(0, 14)
        )
        bind_auto_wrap(
            source_frame, self.lbl_status, horizontal_padding=28, min_wrap=220
        )

        body = tk.Frame(self, bg=self.theme["page_bg"])
        body.grid(row=1, column=0, sticky="nsew")
        body.grid_columnconfigure(0, weight=5)
        body.grid_columnconfigure(1, weight=3)
        body.grid_rowconfigure(0, weight=1)

        left_column = tk.Frame(body, bg=self.theme["page_bg"])
        left_column.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        left_column.grid_columnconfigure(0, weight=1)
        left_column.grid_rowconfigure(1, weight=1)

        self.scan_panel = Surface(left_column, self.theme, variant="panel")
        self.scan_panel.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self.scan_panel.grid_columnconfigure(0, weight=1)
        self.scan_panel.grid_columnconfigure(1, weight=1)

        self.scan_header = SectionHeader(
            self.scan_panel,
            self.theme,
            self.i18n.t("downloader.title"),
            self.i18n.t("downloader.subtitle"),
            eyebrow=self.i18n.t("downloader.source"),
        )
        self.scan_header.grid(
            row=0, column=0, columnspan=3, sticky="ew", padx=14, pady=(14, 8)
        )

        self.lbl_vk_hint = ctk.CTkLabel(
            self.scan_panel,
            text=self.i18n.t("downloader.vk.settings.hint"),
            text_color=self.theme["muted"],
            font=ui_font(self.theme, 12, alt=True),
            anchor="w",
            justify="left",
            wraplength=560,
        )
        self.lbl_vk_hint.grid(
            row=1, column=0, columnspan=3, sticky="ew", padx=14, pady=(0, 12)
        )
        bind_auto_wrap(
            self.scan_panel, self.lbl_vk_hint, horizontal_padding=28, min_wrap=220
        )

        self.btn_scan_vk = ctk.CTkButton(
            self.scan_panel,
            text=self.i18n.t("downloader.scan.vk"),
            command=self.controller.scan_playlists,
            font=ui_font(self.theme, 13, "bold"),
            corner_radius=10,
            height=42,
            **button_style(self.theme, "secondary"),
        )
        self.btn_scan_vk.grid(row=2, column=0, sticky="ew", padx=(14, 8), pady=(0, 14))

        self.btn_scan_yandex = ctk.CTkButton(
            self.scan_panel,
            text=self.i18n.t("downloader.scan.yandex"),
            command=self.controller.scan_yandex_chart,
            font=ui_font(self.theme, 13, "bold"),
            corner_radius=10,
            height=42,
            **button_style(self.theme, "secondary"),
        )
        self.btn_scan_yandex.grid(
            row=2, column=1, sticky="ew", padx=(8, 14), pady=(0, 14)
        )

        playlist_shell = Surface(left_column, self.theme, variant="panel")
        playlist_shell.grid(row=1, column=0, sticky="nsew")
        playlist_shell.grid_rowconfigure(1, weight=1)
        playlist_shell.grid_columnconfigure(0, weight=1)

        self.playlist_header = SectionHeader(
            playlist_shell,
            self.theme,
            self.i18n.t("downloader.playlists"),
            self.i18n.t("downloader.count", selected=0, total=0),
        )
        self.playlist_header.grid(row=0, column=0, sticky="ew", padx=14, pady=(14, 10))

        self.scroll = ctk.CTkScrollableFrame(
            playlist_shell,
            label_text="",
            fg_color=self.theme["panel"],
            corner_radius=12,
            border_width=1,
            border_color=self.theme["border_soft"],
        )
        self.scroll.grid(row=1, column=0, sticky="nsew", padx=14, pady=(0, 14))

        right_column = tk.Frame(body, bg=self.theme["page_bg"])
        right_column.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        right_column.grid_columnconfigure(0, weight=1)

        summary_card = Surface(right_column, self.theme, variant="surface")
        summary_card.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self.summary_header = SectionHeader(
            summary_card,
            self.theme,
            self.i18n.t("downloader.start"),
            self.i18n.t("downloader.count", selected=0, total=0),
        )
        self.summary_header.pack(fill="x", padx=14, pady=(14, 8))
        self.lbl_selected = ctk.CTkLabel(
            summary_card,
            text=self.i18n.t("downloader.count", selected=0, total=0),
            text_color=self.theme["muted"],
            font=ui_font(self.theme, 12, alt=True),
            justify="left",
            anchor="w",
        )
        self.lbl_selected.pack(fill="x", padx=14, pady=(0, 10))
        self.btn_start = ctk.CTkButton(
            summary_card,
            text=self.i18n.t("downloader.start"),
            height=48,
            font=ui_font(self.theme, 14, "bold"),
            command=self.on_start,
            corner_radius=12,
            **button_style(self.theme, "success"),
        )
        self.btn_start.pack(fill="x", padx=14, pady=(0, 14))

        opts_frame = Surface(right_column, self.theme, variant="surface")
        opts_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        self.lbl_options = ctk.CTkLabel(
            opts_frame,
            text=self.i18n.t("downloader.options"),
            font=ui_font(self.theme, 12, "bold", alt=True),
            text_color=self.theme["muted"],
            anchor="w",
        )
        self.lbl_options.pack(fill="x", padx=14, pady=(14, 4))

        self.var_covers = ctk.BooleanVar(value=True)
        self.var_id3 = ctk.BooleanVar(value=True)

        self.chk_covers = ctk.CTkCheckBox(
            opts_frame,
            text=self.i18n.t("downloader.covers"),
            variable=self.var_covers,
            font=ui_font(self.theme, 13, alt=True),
            **checkbox_style(self.theme),
        )
        self.chk_covers.pack(anchor="w", padx=14, pady=(6, 4))
        self.chk_id3 = ctk.CTkCheckBox(
            opts_frame,
            text=self.i18n.t("downloader.id3"),
            variable=self.var_id3,
            font=ui_font(self.theme, 13, alt=True),
            **checkbox_style(self.theme),
        )
        self.chk_id3.pack(anchor="w", padx=14, pady=(0, 14))

        ym_frame = Surface(right_column, self.theme, variant="surface")
        ym_frame.grid(row=2, column=0, sticky="ew")

        self.lbl_ym_header = ctk.CTkLabel(
            ym_frame,
            text=self.i18n.t("downloader.ym.header"),
            font=ui_font(self.theme, 12, "bold", alt=True),
            text_color=self.theme["muted"],
            anchor="w",
        )
        self.lbl_ym_header.pack(fill="x", padx=14, pady=(14, 4))

        ym_url_row = tk.Frame(ym_frame, bg=self.theme["surface"])
        ym_url_row.pack(fill="x", padx=14, pady=(0, 14))
        ym_url_row.grid_columnconfigure(0, weight=1)

        self.ym_url_entry = ctk.CTkEntry(
            ym_url_row,
            placeholder_text=self.i18n.t("downloader.ym.url.placeholder"),
            font=ui_font(self.theme, 12, alt=True),
            height=36,
            corner_radius=8,
        )
        self.ym_url_entry.grid(row=0, column=0, sticky="ew", pady=(0, 8))

        self.btn_ym_scan_url = ctk.CTkButton(
            ym_url_row,
            text=self.i18n.t("downloader.ym.scan.playlist"),
            command=self._on_scan_yandex_url,
            font=ui_font(self.theme, 12, "bold"),
            corner_radius=8,
            height=36,
            **button_style(self.theme, "secondary"),
        )
        self.btn_ym_scan_url.grid(row=1, column=0, sticky="ew")

        self._update_source_controls()

    def update_playlists(self, playlists):
        self.all_playlists = playlists or []
        visible_playlists = [
            pl for pl in self.all_playlists if self._matches_source(pl)
        ]

        # Clear old
        for item in self.checkboxes:
            item[2].destroy()
        self.checkboxes = []

        # Remove empty state elements if they exist
        if hasattr(self, "lbl_empty"):
            self.lbl_empty.destroy()
            del self.lbl_empty
        if hasattr(self, "btn_empty_scan"):
            self.btn_empty_scan.destroy()
            del self.btn_empty_scan
        if hasattr(self, "btn_empty_scan_ym"):
            self.btn_empty_scan_ym.destroy()
            del self.btn_empty_scan_ym
        if hasattr(self, "btn_empty_scan_vk"):
            self.btn_empty_scan_vk.destroy()
            del self.btn_empty_scan_vk

        if not visible_playlists:
            self.lbl_empty = ctk.CTkLabel(
                self.scroll,
                text=(
                    self.i18n.t("downloader.empty.vk")
                    if self.current_source == "vk"
                    else self.i18n.t("downloader.empty")
                ),
                font=ui_font(self.theme, 16, alt=True),
                text_color=self.theme["muted"],
            )
            self.lbl_empty.pack(pady=(50, 10))
            if self.current_source != "vk":
                self.btn_empty_scan_ym = ctk.CTkButton(
                    self.scroll,
                    text=self.i18n.t("downloader.scan.yandex"),
                    command=self.controller.scan_yandex_chart,
                    **button_style(self.theme, "secondary"),
                )
                self.btn_empty_scan_ym.pack(pady=(0, 10))
            else:
                self.btn_empty_scan_vk = ctk.CTkButton(
                    self.scroll,
                    text=self.i18n.t("downloader.scan.vk"),
                    command=self.controller.scan_playlists,
                    **button_style(self.theme, "secondary"),
                )
                self.btn_empty_scan_vk.pack(pady=(0, 10))
            return

        for pl in visible_playlists:
            var = ctk.BooleanVar()
            cb = ctk.CTkCheckBox(
                self.scroll,
                text=f"{pl.title}",
                variable=var,
                font=ui_font(self.theme, 13, alt=True),
                **checkbox_style(self.theme),
            )
            var.trace_add("write", lambda *_: self.update_selected_counter())
            cb.pack(anchor="w", pady=5)
            # Store ref to pl and var
            self.checkboxes.append((pl, var, cb))

        self.update_selected_counter()

    def _on_scan_yandex_url(self):
        url = self.ym_url_entry.get().strip()
        if url:
            self.controller.scan_yandex_playlist(url)
        else:
            self.controller.on_log(self.i18n.t("downloader.ym.url.error"))

    def _on_source_changed(self, value):
        self.current_source = (
            "vk" if value == self.i18n.t("downloader.source.vk") else "yandex"
        )
        if hasattr(self.controller, "set_preferred_source"):
            self.controller.set_preferred_source(self.current_source)
        self._update_source_controls()
        self.update_playlists(self.all_playlists)

    def apply_preferred_source(self):
        preferred = (
            self.controller.get_preferred_source()
            if hasattr(self.controller, "get_preferred_source")
            else "vk"
        )
        self.set_source(preferred)

    def set_source(self, source):
        normalized = source if source in ("vk", "yandex") else "vk"
        self.current_source = normalized
        self.source_selector.set(
            self.i18n.t("downloader.source.vk")
            if normalized == "vk"
            else self.i18n.t("downloader.source.yandex")
        )
        self._update_source_controls()
        self.update_playlists(self.all_playlists)

    def on_show(self):
        preferred = (
            self.controller.get_preferred_source()
            if hasattr(self.controller, "get_preferred_source")
            else "vk"
        )
        if preferred != self.current_source:
            self.set_source(preferred)

    def _matches_source(self, playlist):
        is_yandex = str(getattr(playlist, "id", "")).startswith(
            "ym:"
        ) or "music.yandex.ru" in (getattr(playlist, "url", "") or "")
        return (not is_yandex) if self.current_source == "vk" else is_yandex

    def _update_source_controls(self):
        is_vk = self.current_source == "vk"
        self.lbl_vk_hint.configure(
            text=(
                self.i18n.t("downloader.vk.settings.hint")
                if is_vk
                else self.i18n.t("downloader.ym.hint")
            )
        )
        self.btn_scan_vk.configure(state="normal" if is_vk else "disabled")
        self.btn_scan_yandex.configure(state="disabled" if is_vk else "normal")
        self.ym_url_entry.configure(state="disabled" if is_vk else "normal")
        self.btn_ym_scan_url.configure(state="disabled" if is_vk else "normal")

    def on_start(self):
        selected = []
        for pl, var, cb in self.checkboxes:
            if var.get():
                selected.append(pl)

        if not selected:
            # Maybe log error to controller?
            self.controller.on_log(self.i18n.t("downloader.select.error"))
            return

        settings = {
            "use_covers": self.var_covers.get(),
            "use_id3": self.var_id3.get(),
            # Fetch strategy dynamically from controller which gets it from UI
            "strategy": self.controller.get_current_strategy(),
        }

        self.controller.start_download(selected, settings)

    def set_connected_status(self, connected):
        self.is_connected = connected
        if connected:
            self.lbl_status.configure(
                text=self.i18n.t("app.status.connected"),
                text_color=self.theme["success"],
            )
        else:
            self.lbl_status.configure(
                text=self.i18n.t("downloader.status.idle"),
                text_color=self.theme["muted"],
            )

    def update_selected_counter(self):
        total = len(self.checkboxes)
        selected = sum(1 for _, var, _ in self.checkboxes if var.get())
        summary = self.i18n.t("downloader.count", selected=selected, total=total)
        self.lbl_selected.configure(text=summary)
        self.playlist_header.configure_content(description=summary)
        self.summary_header.configure_content(description=summary)

    def apply_language(self):
        set_resize_lock(True)
        self.scan_header.configure_content(
            title=self.i18n.t("downloader.title"),
            description=self.i18n.t("downloader.subtitle"),
            eyebrow=self.i18n.t("downloader.source"),
        )
        self.lbl_source.configure(text=self.i18n.t("downloader.source"))
        self.source_selector.configure(
            values=[
                self.i18n.t("downloader.source.vk"),
                self.i18n.t("downloader.source.yandex"),
            ]
        )
        self.source_selector.set(
            self.i18n.t("downloader.source.vk")
            if self.current_source == "vk"
            else self.i18n.t("downloader.source.yandex")
        )
        self.lbl_vk_hint.configure(
            text=(
                self.i18n.t("downloader.vk.settings.hint")
                if self.current_source == "vk"
                else self.i18n.t("downloader.ym.hint")
            )
        )
        self.btn_scan_vk.configure(text=self.i18n.t("downloader.scan.vk"))
        self.btn_scan_yandex.configure(text=self.i18n.t("downloader.scan.yandex"))
        self.set_connected_status(self.is_connected)
        self.lbl_options.configure(text=self.i18n.t("downloader.options"))
        self.chk_covers.configure(text=self.i18n.t("downloader.covers"))
        self.chk_id3.configure(text=self.i18n.t("downloader.id3"))
        self.update_selected_counter()
        self.playlist_header.configure_content(
            title=self.i18n.t("downloader.playlists")
        )
        self.summary_header.configure_content(title=self.i18n.t("downloader.start"))
        self.btn_start.configure(text=self.i18n.t("downloader.start"))
        self.lbl_ym_header.configure(text=self.i18n.t("downloader.ym.header"))
        self.ym_url_entry.configure(
            placeholder_text=self.i18n.t("downloader.ym.url.placeholder")
        )
        self.btn_ym_scan_url.configure(text=self.i18n.t("downloader.ym.scan.playlist"))
        if hasattr(self, "lbl_empty"):
            self.lbl_empty.configure(
                text=(
                    self.i18n.t("downloader.empty.vk")
                    if self.current_source == "vk"
                    else self.i18n.t("downloader.empty")
                )
            )
        if hasattr(self, "btn_empty_scan_ym"):
            self.btn_empty_scan_ym.configure(text=self.i18n.t("downloader.scan.yandex"))
        if hasattr(self, "btn_empty_scan_vk"):
            self.btn_empty_scan_vk.configure(text=self.i18n.t("downloader.scan.vk"))
        self._update_source_controls()
        set_resize_lock(False)
        flush_pending_wraps()
