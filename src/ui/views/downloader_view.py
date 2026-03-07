import customtkinter as ctk


class DownloaderView(ctk.CTkFrame):
    def __init__(self, master, controller, i18n, theme):
        super().__init__(master, fg_color="transparent")
        self.controller = controller
        self.i18n = i18n
        self.theme = theme
        self.is_connected = False
        self.checkboxes = []
        self.setup_ui()

    def setup_ui(self):
        self.lbl_title = ctk.CTkLabel(
            self,
            text=self.i18n.t("downloader.title"),
            font=ctk.CTkFont(family=self.theme["font"], size=24, weight="bold"),
            text_color=self.theme["text"],
            anchor="w",
        )
        self.lbl_title.pack(fill="x", padx=8, pady=(6, 0))

        self.lbl_subtitle = ctk.CTkLabel(
            self,
            text=self.i18n.t("downloader.subtitle"),
            font=ctk.CTkFont(family=self.theme["font_fallback"], size=12),
            text_color=self.theme["muted"],
            anchor="w",
        )
        self.lbl_subtitle.pack(fill="x", padx=8, pady=(0, 12))

        ctrl_frame = ctk.CTkFrame(
            self,
            fg_color=self.theme["panel"],
            corner_radius=12,
            border_width=1,
            border_color=self.theme["border"],
        )
        ctrl_frame.pack(fill="x", padx=6, pady=(0, 10))
        
        self.btn_login = ctk.CTkButton(
            ctrl_frame,
            text=self.i18n.t("downloader.login"),
            command=self.controller.start_browser_and_login,
            fg_color=self.theme["accent"],
            hover_color=self.theme["accent_hover"],
            font=ctk.CTkFont(family=self.theme["font"], size=13, weight="bold"),
            corner_radius=10,
            height=42,
        )
        self.btn_login.pack(side="left", padx=12, pady=12)
        
        self.btn_scan = ctk.CTkButton(
            ctrl_frame,
            text=self.i18n.t("downloader.scan"),
            command=self.controller.scan_playlists,
            fg_color="#334155",
            hover_color="#475569",
            font=ctk.CTkFont(family=self.theme["font"], size=13, weight="bold"),
            corner_radius=10,
            height=42,
        )
        self.btn_scan.pack(side="left", padx=0, pady=12)
        
        self.lbl_status = ctk.CTkLabel(
            ctrl_frame,
            text=self.i18n.t("downloader.status.idle"),
            text_color=self.theme["muted"],
            font=ctk.CTkFont(family=self.theme["font_fallback"], size=13),
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
            font=ctk.CTkFont(family=self.theme["font_fallback"], size=12, weight="bold"),
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
            font=ctk.CTkFont(family=self.theme["font_fallback"], size=13),
        )
        self.chk_covers.pack(side="left", padx=12, pady=(6, 10))
        self.chk_id3 = ctk.CTkCheckBox(
            opts_frame,
            text=self.i18n.t("downloader.id3"),
            variable=self.var_id3,
            font=ctk.CTkFont(family=self.theme["font_fallback"], size=13),
        )
        self.chk_id3.pack(side="left", padx=8, pady=(6, 10))

        self.lbl_selected = ctk.CTkLabel(
            opts_frame,
            text=self.i18n.t("downloader.count", selected=0, total=0),
            text_color=self.theme["muted"],
            font=ctk.CTkFont(family=self.theme["font_fallback"], size=12),
        )
        self.lbl_selected.pack(side="right", padx=12, pady=(6, 10))

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
            fg_color=self.theme["success"],
            hover_color="#15803d",
            font=ctk.CTkFont(family=self.theme["font"], size=15, weight="bold"),
            command=self.on_start,
            corner_radius=12,
        )
        self.btn_start.pack(fill="x", padx=6, pady=(12, 2))

    def update_playlists(self, playlists):
        # Clear old
        for item in self.checkboxes:
            item[2].destroy()
        self.checkboxes = []
        
        # Remove empty state elements if they exist
        if hasattr(self, 'lbl_empty'):
            self.lbl_empty.destroy()
            del self.lbl_empty
        if hasattr(self, 'btn_empty_scan'): 
            self.btn_empty_scan.destroy()
            del self.btn_empty_scan
            
        if not playlists:
            self.lbl_empty = ctk.CTkLabel(
                self.scroll,
                text=self.i18n.t("downloader.empty"),
                font=ctk.CTkFont(family=self.theme["font"], size=16),
                text_color=self.theme["muted"],
            )
            self.lbl_empty.pack(pady=(50, 10))
            self.btn_empty_scan = ctk.CTkButton(
                self.scroll,
                text=self.i18n.t("downloader.scan.vk"),
                command=self.controller.scan_playlists,
            )
            self.btn_empty_scan.pack(pady=10)
            return
        
        for pl in playlists:
            var = ctk.BooleanVar()
            cb = ctk.CTkCheckBox(self.scroll, text=f"{pl.title}", variable=var)
            var.trace_add("write", lambda *_: self.update_selected_counter())
            cb.pack(anchor="w", pady=5)
            # Store ref to pl and var
            self.checkboxes.append((pl, var, cb))

        self.update_selected_counter()

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
            "strategy": self.controller.get_current_strategy()
        }
        
        self.controller.start_download(selected, settings)

    def set_connected_status(self, connected):
        self.is_connected = connected
        if connected:
            self.lbl_status.configure(text=self.i18n.t("app.status.connected"), text_color=self.theme["success"])
        else:
            self.lbl_status.configure(text=self.i18n.t("downloader.status.idle"), text_color=self.theme["muted"])

    def update_selected_counter(self):
        total = len(self.checkboxes)
        selected = sum(1 for _, var, _ in self.checkboxes if var.get())
        self.lbl_selected.configure(text=self.i18n.t("downloader.count", selected=selected, total=total))

    def apply_language(self):
        self.lbl_title.configure(text=self.i18n.t("downloader.title"))
        self.lbl_subtitle.configure(text=self.i18n.t("downloader.subtitle"))
        self.btn_login.configure(text=self.i18n.t("downloader.login"))
        self.btn_scan.configure(text=self.i18n.t("downloader.scan"))
        self.set_connected_status(self.is_connected)
        self.lbl_options.configure(text=self.i18n.t("downloader.options"))
        self.chk_covers.configure(text=self.i18n.t("downloader.covers"))
        self.chk_id3.configure(text=self.i18n.t("downloader.id3"))
        self.update_selected_counter()
        self.scroll.configure(label_text=self.i18n.t("downloader.playlists"))
        self.btn_start.configure(text=self.i18n.t("downloader.start"))
        if hasattr(self, "lbl_empty"):
            self.lbl_empty.configure(text=self.i18n.t("downloader.empty"))
        if hasattr(self, "btn_empty_scan"):
            self.btn_empty_scan.configure(text=self.i18n.t("downloader.scan.vk"))
