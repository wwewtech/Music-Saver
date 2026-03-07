import customtkinter as ctk

class DownloaderView(ctk.CTkFrame):
    def __init__(self, master, controller):
        super().__init__(master, fg_color="transparent")
        self.controller = controller
        self.checkboxes = []
        self.setup_ui()

    def setup_ui(self):
        # Controls Frame
        ctrl_frame = ctk.CTkFrame(self)
        ctrl_frame.pack(fill="x", padx=20, pady=10)
        
        btn_login = ctk.CTkButton(ctrl_frame, text="1. Login VK", command=self.controller.start_browser_and_login)
        btn_login.pack(side="left", padx=10, pady=10)
        
        btn_scan = ctk.CTkButton(ctrl_frame, text="2. Scan Playlists", command=self.controller.scan_playlists)
        btn_scan.pack(side="left", padx=10, pady=10)
        
        self.lbl_status = ctk.CTkLabel(ctrl_frame, text="Status: Idle")
        self.lbl_status.pack(side="left", padx=20)

        # Options
        opts_frame = ctk.CTkFrame(self, fg_color="transparent")
        opts_frame.pack(fill="x", padx=20)
        
        self.var_covers = ctk.BooleanVar(value=True)
        self.var_id3 = ctk.BooleanVar(value=True)
        
        ctk.CTkCheckBox(opts_frame, text="Embed Covers", variable=self.var_covers).pack(side="left", padx=10)
        ctk.CTkCheckBox(opts_frame, text="ID3 Tags", variable=self.var_id3).pack(side="left", padx=10)

        # Playlist Area
        self.scroll = ctk.CTkScrollableFrame(self, label_text="Playlists Found")
        self.scroll.pack(fill="both", expand=True, padx=20, pady=10)

        # Action Button
        self.btn_start = ctk.CTkButton(self, text="3. START PROCESSING", height=50, fg_color="green", font=("Roboto", 16, "bold"), command=self.on_start)
        self.btn_start.pack(fill="x", padx=20, pady=20)

    def update_playlists(self, playlists):
        # Clear old
        for cb in self.checkboxes:
            cb.destroy()
        self.checkboxes = []
        
        for pl in playlists:
            var = ctk.BooleanVar()
            cb = ctk.CTkCheckBox(self.scroll, text=f"{pl.title}", variable=var)
            cb.pack(anchor="w", pady=5)
            # Store ref to pl and var
            self.checkboxes.append((pl, var, cb))

    def on_start(self):
        selected = []
        for pl, var, cb in self.checkboxes:
            if var.get():
                selected.append(pl)
        
        if not selected:
            # Maybe log error to controller?
            self.controller.on_log("Пожалуйста, выберите хотя бы один плейлист.")
            return
            
        settings = {
            "use_covers": self.var_covers.get(),
            "use_id3": self.var_id3.get(),
            # Fetch strategy dynamically from controller which gets it from UI
            "strategy": self.controller.get_current_strategy()
        }
        
        self.controller.start_download(selected, settings)
