import tkinter as tk
import customtkinter as ctk
from src.ui.components.primitives import SectionHeader, Surface, bind_auto_wrap, set_resize_lock, flush_pending_wraps
from src.ui.design_system import button_style, combo_style, entry_style, ui_font


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
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.content = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            corner_radius=0,
        )
        self.content.grid(row=0, column=0, sticky="nsew")
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_columnconfigure(1, weight=1)

        source_frame = Surface(self.content, self.theme, variant="surface")
        source_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 12))
        source_frame.grid_columnconfigure(0, weight=1)

        self.source_header = SectionHeader(
            source_frame,
            self.theme,
            self.i18n.t("telegram.source.section"),
            self.i18n.t("telegram.guide.body"),
            eyebrow=self.i18n.t("telegram.title"),
        )
        self.source_header.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 10))

        source_values = self._build_source_values()
        self.seg_source = ctk.CTkSegmentedButton(
            source_frame,
            values=source_values,
            command=self.on_source_change,
            height=34,
            font=ui_font(self.theme, 12, "bold"),
        )
        self.seg_source.grid(row=1, column=0, sticky="w", padx=16, pady=(0, 8))

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
        self.lbl_source_hint.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 16))
        bind_auto_wrap(source_frame, self.lbl_source_hint, horizontal_padding=32, min_wrap=220)
        self._apply_source_hint()

        vk_frame = Surface(self.content, self.theme, variant="surface")
        vk_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 8), pady=(0, 12))

        self.vk_header = SectionHeader(
            vk_frame,
            self.theme,
            self.i18n.t("telegram.vk.section"),
            self.i18n.t("telegram.vk.tip"),
        )
        self.vk_header.pack(fill="x", padx=16, pady=(16, 8))

        self.lbl_vk = self.vk_header.title
        self.lbl_vk_tip = self.vk_header.description

        vk_btn_row = tk.Frame(vk_frame, bg=self.theme["surface"])
        vk_btn_row.pack(fill="x", padx=12, pady=(0, 14))
        vk_btn_row.grid_columnconfigure(0, weight=1)
        vk_btn_row.grid_columnconfigure(1, weight=1)

        self.btn_vk_login = ctk.CTkButton(
            vk_btn_row,
            text=self.i18n.t("telegram.vk.login"),
            command=self.on_vk_login,
            corner_radius=10,
            height=40,
            **button_style(self.theme, "primary"),
        )
        self.btn_vk_login.grid(row=0, column=0, padx=5, pady=(0, 8), sticky="ew")

        self.btn_vk_scan = ctk.CTkButton(
            vk_btn_row,
            text=self.i18n.t("telegram.vk.scan"),
            command=self.on_vk_scan,
            corner_radius=10,
            height=40,
            **button_style(self.theme, "secondary"),
        )
        self.btn_vk_scan.grid(row=0, column=1, padx=5, pady=(0, 8), sticky="ew")

        self.lbl_vk_status = ctk.CTkLabel(
            vk_btn_row,
            text=self.i18n.t("telegram.vk.status.idle"),
            text_color=self.theme["muted"],
            font=ui_font(self.theme, 12, alt=True),
            anchor="w",
            justify="left",
        )
        self.lbl_vk_status.grid(row=1, column=0, columnspan=2, padx=5, sticky="ew")
        bind_auto_wrap(vk_btn_row, self.lbl_vk_status, horizontal_padding=12, min_wrap=180)

        ym_frame = Surface(self.content, self.theme, variant="surface")
        ym_frame.grid(row=1, column=1, sticky="nsew", padx=(8, 0), pady=(0, 12))

        self.ym_header = SectionHeader(
            ym_frame,
            self.theme,
            self.i18n.t("telegram.ym.section"),
            self.i18n.t("telegram.ym.tip"),
        )
        self.ym_header.pack(fill="x", padx=16, pady=(16, 8))

        self.lbl_ym = self.ym_header.title
        self.lbl_ym_tip = self.ym_header.description

        ym_btn_row = tk.Frame(ym_frame, bg=self.theme["surface"])
        ym_btn_row.pack(fill="x", padx=12, pady=(0, 14))
        ym_btn_row.grid_columnconfigure(0, weight=1)

        self.btn_ym_scan = ctk.CTkButton(
            ym_btn_row,
            text=self.i18n.t("telegram.ym.scan"),
            command=self.on_yandex_scan,
            corner_radius=10,
            height=40,
            **button_style(self.theme, "secondary"),
        )
        self.btn_ym_scan.grid(row=0, column=0, padx=5, pady=(0, 8), sticky="w")

        self.lbl_ym_status = ctk.CTkLabel(
            ym_btn_row,
            text=self.i18n.t("telegram.ym.status.idle"),
            text_color=self.theme["muted"],
            font=ui_font(self.theme, 12, alt=True),
            anchor="w",
            justify="left",
        )
        self.lbl_ym_status.grid(row=1, column=0, padx=5, sticky="ew")
        bind_auto_wrap(ym_btn_row, self.lbl_ym_status, horizontal_padding=12, min_wrap=180)

        conn_frame = Surface(self.content, self.theme, variant="panel")
        conn_frame.grid(row=2, column=0, sticky="nsew", padx=(0, 8))

        self.conn_header = SectionHeader(
            conn_frame,
            self.theme,
            self.i18n.t("telegram.connection"),
            self.i18n.t("telegram.tip"),
        )
        self.conn_header.pack(fill="x", padx=16, pady=(16, 8))

        self.lbl_conn = self.conn_header.title

        self.lbl_token, self.entry_token = self.create_input(
            conn_frame, self.i18n.t("telegram.token"), show="*"
        )
        self.lbl_chat, self.entry_chat_id = self.create_input(
            conn_frame, self.i18n.t("telegram.chat_id")
        )

        self.lbl_tip = self.conn_header.description

        # Load existing
        curr = self.controller.get_tg_settings()
        self.entry_token.insert(0, curr.get("tg_bot_token", "") or "")
        self.entry_chat_id.insert(0, curr.get("tg_chat_id", "") or "")

        # Save & Test
        btn_frame = tk.Frame(conn_frame, bg=self.theme["panel"])
        btn_frame.pack(fill="x", padx=14, pady=(4, 14))
        btn_frame.grid_columnconfigure(0, weight=1)
        btn_frame.grid_columnconfigure(1, weight=1)

        self.btn_save = ctk.CTkButton(
            btn_frame,
            text=self.i18n.t("telegram.save"),
            command=self.save_settings,
            corner_radius=10,
            height=40,
            **button_style(self.theme, "primary"),
        )
        self.btn_save.grid(row=0, column=0, padx=5, sticky="ew")
        self.btn_test = ctk.CTkButton(
            btn_frame,
            text=self.i18n.t("telegram.test"),
            command=self.test_connection,
            corner_radius=10,
            height=40,
            **button_style(self.theme, "warning"),
        )
        self.btn_test.grid(row=0, column=1, padx=5, sticky="ew")

        strat_frame = Surface(self.content, self.theme, variant="surface")
        strat_frame.grid(row=2, column=1, sticky="nsew", padx=(8, 0))

        self.strategy_header = SectionHeader(
            strat_frame,
            self.theme,
            self.i18n.t("telegram.strategy"),
            self.i18n.t("telegram.strategy.help"),
        )
        self.strategy_header.pack(fill="x", padx=16, pady=(16, 10))

        self.lbl_strategy = self.strategy_header.title

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
        self.combo_strategy.pack(fill="x", padx=16, pady=(0, 8))

        self.lab_help = self.strategy_header.description

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
        set_resize_lock(True)
        selected_source = self.get_selected_source()
        source_values = self._build_source_values()
        selected_code = self.get_strategy()
        new_values = self._build_strategy_values()

        self.source_header.configure_content(
            title=self.i18n.t("telegram.source.section"),
            description=self.i18n.t("telegram.guide.body"),
            eyebrow=self.i18n.t("telegram.title"),
        )
        self.seg_source.configure(values=source_values)
        self.seg_source.set(
            self.source_code_to_label.get(
                selected_source, self.source_code_to_label["vk"]
            )
        )
        self._apply_source_hint()

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
        set_resize_lock(False)
        flush_pending_wraps()
