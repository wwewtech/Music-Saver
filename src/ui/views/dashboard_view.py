import customtkinter as ctk

class DashboardView(ctk.CTkFrame):
    def __init__(self, master, controller):
        super().__init__(master, fg_color="transparent")
        self.controller = controller
        self.setup_ui()

    def setup_ui(self):
        # Header
        self.lbl_title = ctk.CTkLabel(self, text="Admin Dashboard", font=("Roboto", 24, "bold"))
        self.lbl_title.pack(anchor="w", pady=20, padx=20)

        # Stats Container
        self.stats_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.stats_frame.pack(fill="x", padx=20)
        self.stats_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.card_total = self.create_stat_card(self.stats_frame, "Total Playlists", "0", 0)
        self.card_downloaded = self.create_stat_card(self.stats_frame, "Tracks Downloaded", "0", 1)
        self.card_uploaded = self.create_stat_card(self.stats_frame, "Uploaded to TG", "0", 2)
        self.card_storage = self.create_stat_card(self.stats_frame, "Storage Used", "0 MB", 3)
        
        # Activity Stream (Simplified as label for now, or text box)
        self.lbl_activity = ctk.CTkLabel(self, text="System Status: Ready", font=("Roboto", 16))
        self.lbl_activity.pack(anchor="w", pady=(30, 10), padx=20)
        
    def create_stat_card(self, parent, title, value, col):
        card = ctk.CTkFrame(parent)
        card.grid(row=0, column=col, padx=10, pady=10, sticky="nsew")
        
        lbl_val = ctk.CTkLabel(card, text=value, font=("Roboto", 28, "bold"), text_color="#1f6aa5")
        lbl_val.pack(pady=(20, 5))
        
        lbl_title = ctk.CTkLabel(card, text=title, font=("Roboto", 14), text_color="gray")
        lbl_title.pack(pady=(0, 20))
        return lbl_val

    def update_stats(self):
        stats = self.controller.get_dashboard_stats()
        self.card_total.configure(text=str(stats.get("playlists", 0)))
        self.card_downloaded.configure(text=str(stats.get("tracks_downloaded", 0)))
        self.card_uploaded.configure(text=str(stats.get("tracks_uploaded", 0)))
        self.card_storage.configure(text=f"{stats.get('storage_mb', 0)} MB")
