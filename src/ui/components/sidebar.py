import customtkinter as ctk


class SideBar(ctk.CTkFrame):
    def __init__(self, master, on_login, on_scan, **kwargs):
        super().__init__(master, width=200, corner_radius=0, **kwargs)

        self.on_login = on_login
        self.on_scan = on_scan

        ctk.CTkLabel(
            self, text="VK SAVER", font=ctk.CTkFont(size=20, weight="bold")
        ).pack(pady=20)

        self.btn_login = ctk.CTkButton(
            self, text="1. Войти", command=self._handle_login
        )
        self.btn_login.pack(pady=10, padx=20)

        self.btn_scan = ctk.CTkButton(
            self, text="2. Найти плейлисты", command=self._handle_scan, state="disabled"
        )
        self.btn_scan.pack(pady=10, padx=20)

        ctk.CTkLabel(self, text="Опции:", anchor="w").pack(
            pady=(20, 5), padx=20, fill="x"
        )

        self.sw_covers = ctk.CTkSwitch(self, text="HD Обложки")
        self.sw_covers.select()
        self.sw_covers.pack(padx=20, pady=5)

        self.sw_tags = ctk.CTkSwitch(self, text="ID3 Теги")
        self.sw_tags.select()
        self.sw_tags.pack(padx=20, pady=5)

        # Telegram Section
        ctk.CTkLabel(self, text="Telegram (Status):", anchor="w").pack(
            pady=(20, 5), padx=20, fill="x"
        )

        self.entry_bot_token = ctk.CTkEntry(self, placeholder_text="Bot Token")
        self.entry_bot_token.pack(padx=20, pady=5)

        self.entry_chat_id = ctk.CTkEntry(self, placeholder_text="Chat ID")
        self.entry_chat_id.pack(padx=20, pady=5)

        self.btn_save_tg = ctk.CTkButton(
            self, text="Тест / Сохранить", command=self._handle_save_tg, height=30
        )
        self.btn_save_tg.pack(padx=20, pady=10)

        self.on_save_callback = None

    def set_tg_settings(self, token, chat_id):
        self.entry_bot_token.delete(0, "end")
        self.entry_bot_token.insert(0, token or "")
        self.entry_chat_id.delete(0, "end")
        self.entry_chat_id.insert(0, chat_id or "")

    def _handle_save_tg(self):
        token = self.entry_bot_token.get()
        chat_id = self.entry_chat_id.get()
        if self.on_save_callback:
            self.on_save_callback(token, chat_id)

    def _handle_login(self):
        self.btn_login.configure(state="disabled")
        self.on_login()

    def _handle_scan(self):
        self.btn_scan.configure(state="disabled")
        self.on_scan()

    def enable_scan_btn(self):
        self.btn_scan.configure(state="normal")
