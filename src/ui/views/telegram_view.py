import customtkinter as ctk

class TelegramView(ctk.CTkFrame):
    def __init__(self, master, controller):
        super().__init__(master, fg_color="transparent")
        self.controller = controller
        self.setup_ui()

    def setup_ui(self):
        # Settings
        self.add_entry("Bot Token (from @BotFather):", "entry_token", show="*")
        self.add_entry("Chat ID (start with -100 for groups):", "entry_chat_id")
        
        # Load existing
        curr = self.controller.get_tg_settings()
        self.entry_token.insert(0, curr.get("tg_bot_token", "") or "")
        self.entry_chat_id.insert(0, curr.get("tg_chat_id", "") or "")

        # Save & Test
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkButton(btn_frame, text="Save Settings", command=self.save_settings).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Test Connection", command=self.test_connection, fg_color="#E0A719").pack(side="left", padx=5)
        
        # Strategy
        lbl_strat = ctk.CTkLabel(self, text="Upload Strategy:", font=("Roboto", 14, "bold"))
        lbl_strat.pack(anchor="w", padx=20, pady=(20, 5))
        
        self.combo_strategy = ctk.CTkComboBox(self, values=["download_only", "download_upload", "direct_transfer"])
        self.combo_strategy.set("download_upload") # Default
        self.combo_strategy.pack(fill="x", padx=20)
        
        lab_help = ctk.CTkLabel(self, text="direct_transfer = Delete file from PC after upload", text_color="gray")
        lab_help.pack(anchor="w", padx=20)

    def add_entry(self, label, attr_name, show=None):
        ctk.CTkLabel(self, text=label).pack(anchor="w", padx=20, pady=(10,0))
        entry = ctk.CTkEntry(self, show=show)
        entry.pack(fill="x", padx=20, pady=5)
        setattr(self, attr_name, entry)

    def save_settings(self):
        token = self.entry_token.get()
        chat_id = self.entry_chat_id.get()
        success, msg = self.controller.save_tg_settings(token, chat_id)
        self.controller.on_log(msg) 

    def test_connection(self):
        success, msg = self.controller.test_tg_connection()
        self.controller.on_log(f"Test Result: {msg}")

    def get_strategy(self):
        return self.combo_strategy.get()
