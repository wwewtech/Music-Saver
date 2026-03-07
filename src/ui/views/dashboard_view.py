import customtkinter as ctk


class DashboardView(ctk.CTkFrame):
    def __init__(self, master, controller, i18n, theme):
        super().__init__(master, fg_color="transparent")
        self.controller = controller
        self.i18n = i18n
        self.theme = theme
        self.cards = {}
        self.setup_ui()

    def setup_ui(self):
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True)
        self.container.grid_columnconfigure((0, 1), weight=1)

        self.card_total = self.create_stat_card(self.container, "dashboard.total", "0", 0, 0)
        self.card_downloaded = self.create_stat_card(self.container, "dashboard.downloaded", "0", 0, 1)
        self.card_uploaded = self.create_stat_card(self.container, "dashboard.uploaded", "0", 1, 0)
        self.card_storage = self.create_stat_card(self.container, "dashboard.storage", "0 MB", 1, 1)

        self.status_card = ctk.CTkFrame(
            self,
            fg_color=self.theme["surface"],
            corner_radius=14,
            border_width=1,
            border_color=self.theme["border"],
        )
        self.status_card.pack(fill="x", padx=6, pady=(16, 0))

        self.lbl_activity = ctk.CTkLabel(
            self.status_card,
            text=self.i18n.t("dashboard.ready"),
            font=ctk.CTkFont(family=self.theme["font_fallback"], size=14),
            text_color=self.theme["text"],
            anchor="w",
        )
        self.lbl_activity.pack(fill="x", padx=16, pady=(12, 4))

        self.lbl_tip_title = ctk.CTkLabel(
            self.status_card,
            text=self.i18n.t("dashboard.tip.title"),
            font=ctk.CTkFont(family=self.theme["font_fallback"], size=12, weight="bold"),
            text_color=self.theme["muted"],
            anchor="w",
        )
        self.lbl_tip_title.pack(fill="x", padx=16)

        self.lbl_tip_body = ctk.CTkLabel(
            self.status_card,
            text=self.i18n.t("dashboard.tip.body"),
            font=ctk.CTkFont(family=self.theme["font_fallback"], size=13),
            text_color=self.theme["text"],
            anchor="w",
            justify="left",
            wraplength=860,
        )
        self.lbl_tip_body.pack(fill="x", padx=16, pady=(2, 14))
        
    def create_stat_card(self, parent, title_key, value, row, col):
        card = ctk.CTkFrame(
            parent,
            fg_color=self.theme["card"],
            corner_radius=14,
            border_width=1,
            border_color=self.theme["border"],
        )
        card.grid(row=row, column=col, padx=6, pady=6, sticky="nsew")
        
        lbl_val = ctk.CTkLabel(
            card,
            text=value,
            font=ctk.CTkFont(family=self.theme["font"], size=32, weight="bold"),
            text_color=self.theme["accent"],
        )
        lbl_val.pack(anchor="w", padx=18, pady=(16, 0))
        
        lbl_title = ctk.CTkLabel(
            card,
            text=self.i18n.t(title_key),
            font=ctk.CTkFont(family=self.theme["font_fallback"], size=13),
            text_color=self.theme["muted"],
            anchor="w",
        )
        lbl_title.pack(fill="x", padx=18, pady=(2, 14))
        self.cards[title_key] = lbl_title
        return lbl_val

    def apply_language(self):
        self.lbl_activity.configure(text=self.i18n.t("dashboard.ready"))
        self.lbl_tip_title.configure(text=self.i18n.t("dashboard.tip.title"))
        self.lbl_tip_body.configure(text=self.i18n.t("dashboard.tip.body"))
        for key, label in self.cards.items():
            label.configure(text=self.i18n.t(key))

    def update_stats(self):
        stats = self.controller.get_dashboard_stats()
        self.card_total.configure(text=str(stats.get("playlists", 0)))
        self.card_downloaded.configure(text=str(stats.get("tracks_downloaded", 0)))
        self.card_uploaded.configure(text=str(stats.get("tracks_uploaded", 0)))
        self.card_storage.configure(text=f"{stats.get('storage_mb', 0)} MB")
