import customtkinter as ctk


class TelegramView(ctk.CTkFrame):
    def __init__(self, master, controller, i18n, theme):
        super().__init__(master, fg_color="transparent")
        self.controller = controller
        self.i18n = i18n
        self.theme = theme
        self.strategy_codes = ["download_only", "download_upload", "direct_transfer"]
        self.strategy_label_to_code = {}
        self.strategy_code_to_label = {}
        self.setup_ui()

    def setup_ui(self):
        self.lbl_title = ctk.CTkLabel(
            self,
            text=self.i18n.t("telegram.title"),
            font=ctk.CTkFont(family=self.theme["font"], size=24, weight="bold"),
            text_color=self.theme["text"],
            anchor="w",
        )
        self.lbl_title.pack(fill="x", padx=8, pady=(6, 0))

        self.lbl_subtitle = ctk.CTkLabel(
            self,
            text=self.i18n.t("telegram.subtitle"),
            font=ctk.CTkFont(family=self.theme["font_fallback"], size=12),
            text_color=self.theme["muted"],
            anchor="w",
        )
        self.lbl_subtitle.pack(fill="x", padx=8, pady=(0, 12))

        # --- Connection Settings ---
        self.lbl_conn = ctk.CTkLabel(
            self,
            text=self.i18n.t("telegram.connection"),
            font=ctk.CTkFont(family=self.theme["font"], size=18, weight="bold"),
            text_color=self.theme["text"],
        )
        self.lbl_conn.pack(anchor="w", padx=8, pady=(0, 5))
        
        conn_frame = ctk.CTkFrame(
            self,
            fg_color=self.theme["panel"],
            corner_radius=12,
            border_width=1,
            border_color=self.theme["border"],
        )
        conn_frame.pack(fill="x", padx=6)
        
        self.lbl_token, self.entry_token = self.create_input(conn_frame, self.i18n.t("telegram.token"), show="*")
        self.lbl_chat, self.entry_chat_id = self.create_input(conn_frame, self.i18n.t("telegram.chat_id"))
        
        self.lbl_tip = ctk.CTkLabel(
            conn_frame,
            text=self.i18n.t("telegram.tip"),
            text_color=self.theme["muted"],
            font=ctk.CTkFont(family=self.theme["font_fallback"], size=12),
            wraplength=880,
            justify="left",
        )
        self.lbl_tip.pack(anchor="w", padx=20, pady=(0, 10))
        
        # Load existing
        curr = self.controller.get_tg_settings()
        self.entry_token.insert(0, curr.get("tg_bot_token", "") or "")
        self.entry_chat_id.insert(0, curr.get("tg_chat_id", "") or "")

        # Save & Test
        btn_frame = ctk.CTkFrame(conn_frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=10)
        
        self.btn_save = ctk.CTkButton(
            btn_frame,
            text=self.i18n.t("telegram.save"),
            command=self.save_settings,
            fg_color=self.theme["accent"],
            hover_color=self.theme["accent_hover"],
            corner_radius=10,
            height=40,
        )
        self.btn_save.pack(side="left", padx=5)
        self.btn_test = ctk.CTkButton(
            btn_frame,
            text=self.i18n.t("telegram.test"),
            command=self.test_connection,
            fg_color="#b45309",
            hover_color="#92400e",
            corner_radius=10,
            height=40,
        )
        self.btn_test.pack(side="left", padx=5)
        
        # --- Strategy ---
        self.lbl_strategy = ctk.CTkLabel(
            self,
            text=self.i18n.t("telegram.strategy"),
            font=ctk.CTkFont(family=self.theme["font"], size=18, weight="bold"),
            text_color=self.theme["text"],
        )
        self.lbl_strategy.pack(anchor="w", padx=8, pady=(14, 5))
        
        strat_frame = ctk.CTkFrame(
            self,
            fg_color=self.theme["surface"],
            corner_radius=12,
            border_width=1,
            border_color=self.theme["border"],
        )
        strat_frame.pack(fill="x", padx=6)

        strategy_values = self._build_strategy_values()
        
        self.combo_strategy = ctk.CTkComboBox(strat_frame, values=strategy_values, command=self.on_strategy_change)
        initial_strategy = curr.get("processing_strategy", "download_only")
        if initial_strategy not in self.strategy_code_to_label:
            initial_strategy = "download_only"
        self.combo_strategy.set(self.strategy_code_to_label[initial_strategy])
        self.combo_strategy.pack(fill="x", padx=20, pady=(16, 5))
        
        self.lab_help = ctk.CTkLabel(
            strat_frame,
            text=self.i18n.t("telegram.strategy.help"),
            text_color=self.theme["muted"],
            wraplength=780,
            justify="left",
            font=ctk.CTkFont(family=self.theme["font_fallback"], size=12),
        )
        self.lab_help.pack(anchor="w", padx=20, pady=(0, 20))

    def create_input(self, parent, label, show=None):
        label_widget = ctk.CTkLabel(parent, text=label, text_color=self.theme["text"])
        label_widget.pack(anchor="w", padx=20, pady=(10,0))
        entry = ctk.CTkEntry(parent, show=show, height=36, corner_radius=10)
        entry.pack(fill="x", padx=20, pady=5)
        return label_widget, entry

    def _build_strategy_values(self):
        self.strategy_label_to_code = {}
        self.strategy_code_to_label = {}
        values = []
        for code in self.strategy_codes:
            label = self.i18n.t(f"strategy.{code}")
            self.strategy_label_to_code[label] = code
            self.strategy_code_to_label[code] = label
            values.append(label)
        return values

    def save_settings(self):
        token = self.entry_token.get()
        chat_id = self.entry_chat_id.get()
        success, msg = self.controller.save_tg_settings(token, chat_id)
        self.controller.on_log(msg) 

    def test_connection(self):
        success, msg = self.controller.test_tg_connection()
        self.controller.on_log(self.i18n.t("telegram.test.result", msg=msg))

    def get_strategy(self):
        label = self.combo_strategy.get()
        return self.strategy_label_to_code.get(label, "download_upload")

    def on_strategy_change(self, _value):
        strategy = self.get_strategy()
        if hasattr(self.controller, "set_processing_strategy"):
            self.controller.set_processing_strategy(strategy)

    def apply_language(self):
        selected_code = self.get_strategy()
        new_values = self._build_strategy_values()

        self.lbl_title.configure(text=self.i18n.t("telegram.title"))
        self.lbl_subtitle.configure(text=self.i18n.t("telegram.subtitle"))

        self.lbl_conn.configure(text=self.i18n.t("telegram.connection"))
        self.lbl_token.configure(text=self.i18n.t("telegram.token"))
        self.lbl_chat.configure(text=self.i18n.t("telegram.chat_id"))
        self.lbl_tip.configure(text=self.i18n.t("telegram.tip"))
        self.btn_save.configure(text=self.i18n.t("telegram.save"))
        self.btn_test.configure(text=self.i18n.t("telegram.test"))

        self.lbl_strategy.configure(text=self.i18n.t("telegram.strategy"))
        self.combo_strategy.configure(values=new_values)
        self.combo_strategy.set(self.strategy_code_to_label.get(selected_code, self.strategy_code_to_label["download_only"]))
        self.lab_help.configure(text=self.i18n.t("telegram.strategy.help"))
