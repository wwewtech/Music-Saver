import customtkinter as ctk
from src.ui.design_system import ui_font, button_style, checkbox_style


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
        self.lbl_title = ctk.CTkLabel(
            self,
            text=self.i18n.t("downloader.title"),
            font=ui_font(self.theme, 24, "bold"),
            text_color=self.theme["text"],
            anchor="w",
        )
        self.lbl_title.pack(fill="x", padx=8, pady=(6, 0))

        self.lbl_subtitle = ctk.CTkLabel(
            self,
            text=self.i18n.t("downloader.subtitle"),
            font=ui_font(self.theme, 12, alt=True),
            text_color=self.theme["muted"],
            anchor="w",
        )
        self.lbl_subtitle.pack(fill="x", padx=8, pady=(0, 12))

        source_frame = ctk.CTkFrame(
            self,
            fg_color=self.theme["surface"],
            corner_radius=12,
            border_width=1,
            border_color=self.theme["border"],
        )
        source_frame.pack(fill="x", padx=6, pady=(0, 10))

        self.lbl_source = ctk.CTkLabel(
            source_frame,
            text=self.i18n.t("downloader.source"),
            font=ui_font(self.theme, 12, "bold", alt=True),
            text_color=self.theme["muted"],
            anchor="w",
        )
        self.lbl_source.pack(side="left", padx=(12, 8), pady=10)

        self.source_selector = ctk.CTkSegmentedButton(
            source_frame,
            values=[
                self.i18n.t("downloader.source.vk"),
                self.i18n.t("downloader.source.yandex"),
            ],
            command=self._on_source_changed,
            height=32,
            font=ui_font(self.theme, 12, "bold"),
        )
        self.source_selector.pack(side="left", padx=(0, 12), pady=8)
        self.source_selector.set(self.i18n.t("downloader.source.vk"))

        ctrl_frame = ctk.CTkFrame(
            self,
            fg_color=self.theme["panel"],
            corner_radius=12,
            border_width=1,
            border_color=self.theme["border"],
        )
        ctrl_frame.pack(fill="x", padx=6, pady=(0, 10))

        self.lbl_vk_hint = ctk.CTkLabel(
            ctrl_frame,
            text=self.i18n.t("downloader.vk.settings.hint"),
            text_color=self.theme["muted"],
            font=ui_font(self.theme, 12, alt=True),
            anchor="w",
            justify="left",
        )
        self.lbl_vk_hint.pack(side="left", padx=12, pady=12)

        self.btn_scan_yandex = ctk.CTkButton(
            ctrl_frame,
            text=self.i18n.t("downloader.scan.yandex"),
            command=self.controller.scan_yandex_chart,
            font=ui_font(self.theme, 13, "bold"),
            corner_radius=10,
            height=42,
            **button_style(self.theme, "secondary"),
        )
        self.btn_scan_yandex.pack(side="left", padx=8, pady=12)

        self.lbl_status = ctk.CTkLabel(
            ctrl_frame,
            text=self.i18n.t("downloader.status.idle"),
            text_color=self.theme["muted"],
            font=ui_font(self.theme, 13, alt=True),
        )
        self.lbl_status.pack(side="right", padx=14)

        opts_frame = ctk.CTkFrame(
            self,
            fg_color=self.theme["surface"],
            corner_radius=12,
            border_width=1,
            border_color=self.theme["border"],
        )
        opts_frame.pack(fill="x", padx=6, pady=(0, 10))

        self.lbl_options = ctk.CTkLabel(
            opts_frame,
            text=self.i18n.t("downloader.options"),
            font=ui_font(self.theme, 12, "bold", alt=True),
            text_color=self.theme["muted"],
            anchor="w",
        )
        self.lbl_options.pack(fill="x", padx=12, pady=(10, 0))

        self.var_covers = ctk.BooleanVar(value=True)
        self.var_id3 = ctk.BooleanVar(value=True)

        self.chk_covers = ctk.CTkCheckBox(
            opts_frame,
            text=self.i18n.t("downloader.covers"),
            variable=self.var_covers,
            font=ui_font(self.theme, 13, alt=True),
            **checkbox_style(self.theme),
        )
        self.chk_covers.pack(side="left", padx=12, pady=(6, 10))
        self.chk_id3 = ctk.CTkCheckBox(
            opts_frame,
            text=self.i18n.t("downloader.id3"),
            variable=self.var_id3,
            font=ui_font(self.theme, 13, alt=True),
            **checkbox_style(self.theme),
        )
        self.chk_id3.pack(side="left", padx=8, pady=(6, 10))

        self.lbl_selected = ctk.CTkLabel(
            opts_frame,
            text=self.i18n.t("downloader.count", selected=0, total=0),
            text_color=self.theme["muted"],
            font=ui_font(self.theme, 12, alt=True),
        )
        self.lbl_selected.pack(side="right", padx=12, pady=(6, 10))

        # ── Yandex Music Section ────────────────────────────────────────
        ym_frame = ctk.CTkFrame(
            self,
            fg_color=self.theme["surface"],
            corner_radius=12,
            border_width=1,
            border_color=self.theme["border"],
        )
        ym_frame.pack(fill="x", padx=6, pady=(0, 10))

        self.lbl_ym_header = ctk.CTkLabel(
            ym_frame,
            text=self.i18n.t("downloader.ym.header"),
            font=ui_font(self.theme, 12, "bold", alt=True),
            text_color=self.theme["muted"],
            anchor="w",
        )
        self.lbl_ym_header.pack(fill="x", padx=12, pady=(10, 4))

        # URL row
        ym_url_row = ctk.CTkFrame(ym_frame, fg_color="transparent")
        ym_url_row.pack(fill="x", padx=12, pady=(0, 4))

        self.ym_url_entry = ctk.CTkEntry(
            ym_url_row,
            placeholder_text=self.i18n.t("downloader.ym.url.placeholder"),
            font=ui_font(self.theme, 12, alt=True),
            height=36,
            corner_radius=8,
        )
        self.ym_url_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))

        self.btn_ym_scan_url = ctk.CTkButton(
            ym_url_row,
            text=self.i18n.t("downloader.ym.scan.playlist"),
            command=self._on_scan_yandex_url,
            font=ui_font(self.theme, 12, "bold"),
            corner_radius=8,
            height=36,
            **button_style(self.theme, "secondary"),
        )
        self.btn_ym_scan_url.pack(side="left", padx=(0, 0))

        # Playlist Area
        self.scroll = ctk.CTkScrollableFrame(
            self,
            label_text=self.i18n.t("downloader.playlists"),
            fg_color=self.theme["panel"],
            corner_radius=12,
            border_width=1,
            border_color=self.theme["border"],
        )
        self.scroll.pack(fill="both", expand=True, padx=6, pady=0)

        # Action Button
        self.btn_start = ctk.CTkButton(
            self,
            text=self.i18n.t("downloader.start"),
            height=50,
            font=ui_font(self.theme, 15, "bold"),
            command=self.on_start,
            corner_radius=12,
            **button_style(self.theme, "success"),
        )
        self.btn_start.pack(fill="x", padx=6, pady=(12, 2))

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
        self.apply_preferred_source()

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
        self.lbl_selected.configure(
            text=self.i18n.t("downloader.count", selected=selected, total=total)
        )

    def apply_language(self):
        self.lbl_title.configure(text=self.i18n.t("downloader.title"))
        self.lbl_subtitle.configure(text=self.i18n.t("downloader.subtitle"))
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
        self.btn_scan_yandex.configure(text=self.i18n.t("downloader.scan.yandex"))
        self.set_connected_status(self.is_connected)
        self.lbl_options.configure(text=self.i18n.t("downloader.options"))
        self.chk_covers.configure(text=self.i18n.t("downloader.covers"))
        self.chk_id3.configure(text=self.i18n.t("downloader.id3"))
        self.update_selected_counter()
        self.scroll.configure(label_text=self.i18n.t("downloader.playlists"))
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
        self._update_source_controls()
