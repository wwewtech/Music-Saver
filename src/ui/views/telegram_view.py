import customtkinter as ctk
from src.ui.design_system import ui_font, button_style, entry_style, combo_style


class TelegramView(ctk.CTkFrame):
    def __init__(self, master, controller, i18n, theme):
        super().__init__(master, fg_color="transparent")
        self.controller = controller
        self.i18n = i18n
        self.theme = theme
        self.source_codes = ["vk", "yandex"]
        self.source_label_to_code = {}
        self.source_code_to_label = {}
        self.strategy_codes = ["download_only", "download_upload", "direct_transfer"]
        self.strategy_label_to_code = {}
        self.strategy_code_to_label = {}
        self._vk_connected = False
        self._yandex_ready = False
        self.setup_ui()

    def setup_ui(self):
        self.lbl_source_section = ctk.CTkLabel(
            self,
            text=self.i18n.t("telegram.source.section"),
            font=ui_font(self.theme, 18, "bold"),
            text_color=self.theme["text"],
        )
        self.lbl_source_section.pack(anchor="w", padx=8, pady=(8, 5))

        source_frame = ctk.CTkFrame(
            self,
            fg_color=self.theme["surface"],
            corner_radius=12,
            border_width=1,
            border_color=self.theme["border"],
        )
        source_frame.pack(fill="x", padx=6, pady=(0, 12))

        source_values = self._build_source_values()
        self.seg_source = ctk.CTkSegmentedButton(
            source_frame,
            values=source_values,
            command=self.on_source_change,
            height=34,
            font=ui_font(self.theme, 12, "bold"),
        )
        self.seg_source.pack(fill="x", padx=16, pady=(14, 8))

        initial_source = (
            self.controller.get_preferred_source()
            if hasattr(self.controller, "get_preferred_source")
            else "vk"
        )
        if initial_source not in self.source_code_to_label:
            initial_source = "vk"
        self.seg_source.set(self.source_code_to_label[initial_source])

        self.lbl_source_hint = ctk.CTkLabel(
            source_frame,
            text="",
            text_color=self.theme["muted"],
            font=ui_font(self.theme, 12, alt=True),
            justify="left",
            anchor="w",
            wraplength=900,
        )
        self.lbl_source_hint.pack(fill="x", padx=16, pady=(0, 12))
        self._apply_source_hint()

        self.guide_frame = ctk.CTkFrame(
            self,
            fg_color=self.theme["surface"],
            corner_radius=12,
            border_width=1,
            border_color=self.theme["border"],
        )
        self.guide_frame.pack(fill="x", padx=6, pady=(0, 12))

        self.lbl_guide_title = ctk.CTkLabel(
            self.guide_frame,
            text=self.i18n.t("telegram.guide.title"),
            font=ui_font(self.theme, 14, "bold", alt=True),
            text_color=self.theme["text"],
            anchor="w",
        )
        self.lbl_guide_title.pack(fill="x", padx=16, pady=(12, 4))

        self.lbl_guide_body = ctk.CTkLabel(
            self.guide_frame,
            text=self.i18n.t("telegram.guide.body"),
            text_color=self.theme["muted"],
            font=ui_font(self.theme, 12, alt=True),
            justify="left",
            anchor="w",
            wraplength=900,
        )
        self.lbl_guide_body.pack(fill="x", padx=16, pady=(0, 12))

        self.lbl_vk = ctk.CTkLabel(
            self,
            text=self.i18n.t("telegram.vk.section"),
            font=ui_font(self.theme, 18, "bold"),
            text_color=self.theme["text"],
        )
        self.lbl_vk.pack(anchor="w", padx=8, pady=(0, 5))

        vk_frame = ctk.CTkFrame(
            self,
            fg_color=self.theme["surface"],
            corner_radius=12,
            border_width=1,
            border_color=self.theme["border"],
        )
        vk_frame.pack(fill="x", padx=6, pady=(0, 12))

        self.lbl_vk_tip = ctk.CTkLabel(
            vk_frame,
            text=self.i18n.t("telegram.vk.tip"),
            text_color=self.theme["muted"],
            font=ui_font(self.theme, 12, alt=True),
            wraplength=880,
            justify="left",
            anchor="w",
        )
        self.lbl_vk_tip.pack(fill="x", padx=16, pady=(12, 6))

        vk_btn_row = ctk.CTkFrame(vk_frame, fg_color="transparent")
        vk_btn_row.pack(fill="x", padx=10, pady=(0, 10))

        self.btn_vk_login = ctk.CTkButton(
            vk_btn_row,
            text=self.i18n.t("telegram.vk.login"),
            command=self.on_vk_login,
            corner_radius=10,
            height=40,
            **button_style(self.theme, "primary"),
        )
        self.btn_vk_login.pack(side="left", padx=5)

        self.btn_vk_scan = ctk.CTkButton(
            vk_btn_row,
            text=self.i18n.t("telegram.vk.scan"),
            command=self.on_vk_scan,
            corner_radius=10,
            height=40,
            **button_style(self.theme, "secondary"),
        )
        self.btn_vk_scan.pack(side="left", padx=5)

        self.lbl_vk_status = ctk.CTkLabel(
            vk_btn_row,
            text=self.i18n.t("telegram.vk.status.idle"),
            text_color=self.theme["muted"],
            font=ui_font(self.theme, 12, alt=True),
        )
        self.lbl_vk_status.pack(side="right", padx=8)

        self.lbl_ym = ctk.CTkLabel(
            self,
            text=self.i18n.t("telegram.ym.section"),
            font=ui_font(self.theme, 18, "bold"),
            text_color=self.theme["text"],
        )
        self.lbl_ym.pack(anchor="w", padx=8, pady=(0, 5))

        ym_frame = ctk.CTkFrame(
            self,
            fg_color=self.theme["surface"],
            corner_radius=12,
            border_width=1,
            border_color=self.theme["border"],
        )
        ym_frame.pack(fill="x", padx=6, pady=(0, 12))

        self.lbl_ym_tip = ctk.CTkLabel(
            ym_frame,
            text=self.i18n.t("telegram.ym.tip"),
            text_color=self.theme["muted"],
            font=ui_font(self.theme, 12, alt=True),
            wraplength=880,
            justify="left",
            anchor="w",
        )
        self.lbl_ym_tip.pack(fill="x", padx=16, pady=(12, 6))

        ym_btn_row = ctk.CTkFrame(ym_frame, fg_color="transparent")
        ym_btn_row.pack(fill="x", padx=10, pady=(0, 10))

        self.btn_ym_scan = ctk.CTkButton(
            ym_btn_row,
            text=self.i18n.t("telegram.ym.scan"),
            command=self.on_yandex_scan,
            corner_radius=10,
            height=40,
            **button_style(self.theme, "secondary"),
        )
        self.btn_ym_scan.pack(side="left", padx=5)

        self.lbl_ym_status = ctk.CTkLabel(
            ym_btn_row,
            text=self.i18n.t("telegram.ym.status.idle"),
            text_color=self.theme["muted"],
            font=ui_font(self.theme, 12, alt=True),
        )
        self.lbl_ym_status.pack(side="right", padx=8)

        # --- Connection Settings ---
        self.lbl_conn = ctk.CTkLabel(
            self,
            text=self.i18n.t("telegram.connection"),
            font=ui_font(self.theme, 18, "bold"),
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

        self.lbl_token, self.entry_token = self.create_input(
            conn_frame, self.i18n.t("telegram.token"), show="*"
        )
        self.lbl_chat, self.entry_chat_id = self.create_input(
            conn_frame, self.i18n.t("telegram.chat_id")
        )

        self.lbl_tip = ctk.CTkLabel(
            conn_frame,
            text=self.i18n.t("telegram.tip"),
            text_color=self.theme["muted"],
            font=ui_font(self.theme, 12, alt=True),
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
            corner_radius=10,
            height=40,
            **button_style(self.theme, "primary"),
        )
        self.btn_save.pack(side="left", padx=5)
        self.btn_test = ctk.CTkButton(
            btn_frame,
            text=self.i18n.t("telegram.test"),
            command=self.test_connection,
            corner_radius=10,
            height=40,
            **button_style(self.theme, "warning"),
        )
        self.btn_test.pack(side="left", padx=5)

        # --- Strategy ---
        self.lbl_strategy = ctk.CTkLabel(
            self,
            text=self.i18n.t("telegram.strategy"),
            font=ui_font(self.theme, 18, "bold"),
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

        self.combo_strategy = ctk.CTkComboBox(
            strat_frame,
            values=strategy_values,
            command=self.on_strategy_change,
            font=ui_font(self.theme, 13, alt=True),
            **combo_style(self.theme),
        )
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
            font=ui_font(self.theme, 12, alt=True),
        )
        self.lab_help.pack(anchor="w", padx=20, pady=(0, 20))

    def create_input(self, parent, label, show=None):
        label_widget = ctk.CTkLabel(
            parent,
            text=label,
            text_color=self.theme["text"],
            font=ui_font(self.theme, 12, "bold", alt=True),
        )
        label_widget.pack(anchor="w", padx=20, pady=(10, 0))
        entry = ctk.CTkEntry(
            parent,
            show=show,
            height=36,
            font=ui_font(self.theme, 13, alt=True),
            **entry_style(self.theme),
        )
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

    def _build_source_values(self):
        self.source_label_to_code = {}
        self.source_code_to_label = {}
        values = []
        for code in self.source_codes:
            key = "downloader.source.vk" if code == "vk" else "downloader.source.yandex"
            label = self.i18n.t(key)
            self.source_label_to_code[label] = code
            self.source_code_to_label[code] = label
            values.append(label)
        return values

    def get_selected_source(self):
        label = self.seg_source.get()
        return self.source_label_to_code.get(label, "vk")

    def on_source_change(self, _value):
        source = self.get_selected_source()
        if hasattr(self.controller, "set_preferred_source"):
            self.controller.set_preferred_source(source)
        if hasattr(self.controller, "on_preferred_source_changed"):
            self.controller.on_preferred_source_changed(source)
        self._apply_source_hint()

    def _apply_source_hint(self):
        source = self.get_selected_source()
        hint_key = (
            "telegram.source.hint.vk"
            if source == "vk"
            else "telegram.source.hint.yandex"
        )
        self.lbl_source_hint.configure(text=self.i18n.t(hint_key))

    def save_settings(self):
        token = self.entry_token.get()
        chat_id = self.entry_chat_id.get()
        success, msg = self.controller.save_tg_settings(token, chat_id)
        self.controller.on_log(msg)

    def on_vk_login(self):
        self.lbl_vk_status.configure(
            text=self.i18n.t("telegram.vk.status.pending"),
            text_color=self.theme["muted"],
        )
        self.controller.start_browser_and_login()

    def on_vk_scan(self):
        self.controller.scan_playlists()

    def on_yandex_scan(self):
        self.lbl_ym_status.configure(
            text=self.i18n.t("telegram.ym.status.pending"),
            text_color=self.theme["muted"],
        )
        self.controller.scan_yandex_chart()

    def set_vk_connected_status(self, connected):
        self._vk_connected = connected
        if connected:
            self.lbl_vk_status.configure(
                text=self.i18n.t("telegram.vk.status.connected"),
                text_color=self.theme["success"],
            )
        else:
            self.lbl_vk_status.configure(
                text=self.i18n.t("telegram.vk.status.idle"),
                text_color=self.theme["muted"],
            )

    def set_yandex_collection_status(self, ready):
        self._yandex_ready = ready
        if ready:
            self.lbl_ym_status.configure(
                text=self.i18n.t("telegram.ym.status.ready"),
                text_color=self.theme["success"],
            )
        else:
            self.lbl_ym_status.configure(
                text=self.i18n.t("telegram.ym.status.idle"),
                text_color=self.theme["muted"],
            )

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
        selected_source = self.get_selected_source()
        source_values = self._build_source_values()
        selected_code = self.get_strategy()
        new_values = self._build_strategy_values()

        self.lbl_source_section.configure(text=self.i18n.t("telegram.source.section"))
        self.seg_source.configure(values=source_values)
        self.seg_source.set(
            self.source_code_to_label.get(
                selected_source, self.source_code_to_label["vk"]
            )
        )
        self._apply_source_hint()

        self.lbl_guide_title.configure(text=self.i18n.t("telegram.guide.title"))
        self.lbl_guide_body.configure(text=self.i18n.t("telegram.guide.body"))

        self.lbl_vk.configure(text=self.i18n.t("telegram.vk.section"))
        self.lbl_vk_tip.configure(text=self.i18n.t("telegram.vk.tip"))
        self.btn_vk_login.configure(text=self.i18n.t("telegram.vk.login"))
        self.btn_vk_scan.configure(text=self.i18n.t("telegram.vk.scan"))
        self.set_vk_connected_status(self._vk_connected)

        self.lbl_ym.configure(text=self.i18n.t("telegram.ym.section"))
        self.lbl_ym_tip.configure(text=self.i18n.t("telegram.ym.tip"))
        self.btn_ym_scan.configure(text=self.i18n.t("telegram.ym.scan"))
        self.set_yandex_collection_status(self._yandex_ready)

        self.lbl_conn.configure(text=self.i18n.t("telegram.connection"))
        self.lbl_token.configure(text=self.i18n.t("telegram.token"))
        self.lbl_chat.configure(text=self.i18n.t("telegram.chat_id"))
        self.lbl_tip.configure(text=self.i18n.t("telegram.tip"))
        self.btn_save.configure(text=self.i18n.t("telegram.save"))
        self.btn_test.configure(text=self.i18n.t("telegram.test"))

        self.lbl_strategy.configure(text=self.i18n.t("telegram.strategy"))
        self.combo_strategy.configure(values=new_values)
        self.combo_strategy.set(
            self.strategy_code_to_label.get(
                selected_code, self.strategy_code_to_label["download_only"]
            )
        )
        self.lab_help.configure(text=self.i18n.t("telegram.strategy.help"))
