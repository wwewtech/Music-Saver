import customtkinter as ctk
import tkinter.filedialog as filedialog
from tkinter import TclError
import webbrowser
from queue import Queue, Empty

from src.utils.logger import logger
from src.ui.i18n import I18n
from src.ui.design_system import (
    get_theme,
    ui_font,
    button_style,
    entry_style,
    checkbox_style,
)


class WizardStep(ctk.CTkFrame):
    def __init__(self, master, wizard, title_key, description_key):
        super().__init__(master, fg_color="transparent")
        self.wizard = wizard
        self.i18n = wizard.i18n
        self.theme = wizard.theme
        self.title_key = title_key
        self.description_key = description_key
        self._build_base_ui()

    def _build_base_ui(self):
        self.lbl_title = ctk.CTkLabel(
            self,
            text=self.i18n.t(self.title_key),
            font=ctk.CTkFont(family=self.theme["font"], size=26, weight="bold"),
            text_color=self.theme["text"],
            anchor="w",
        )
        self.lbl_title.pack(fill="x", padx=10, pady=(8, 0))

        self.lbl_description = ctk.CTkLabel(
            self,
            text=self.i18n.t(self.description_key),
            font=ctk.CTkFont(family=self.theme["font_fallback"], size=13),
            text_color=self.theme["muted"],
            anchor="w",
            justify="left",
            wraplength=640,
        )
        self.lbl_description.pack(fill="x", padx=10, pady=(4, 12))

        self.content_card = ctk.CTkFrame(
            self,
            fg_color=self.theme["surface"],
            corner_radius=14,
            border_width=1,
            border_color=self.theme["border"],
        )
        self.content_card.pack(fill="both", expand=True, padx=4, pady=(0, 10))

        self.content_frame = ctk.CTkFrame(self.content_card, fg_color="transparent")
        self.content_frame.pack(fill="both", expand=True, padx=18, pady=18)

        self.nav_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.nav_frame.pack(fill="x", padx=4)

        self.btn_back = ctk.CTkButton(
            self.nav_frame,
            text=self.i18n.t("wizard.back"),
            command=self.wizard.prev_step,
            corner_radius=10,
            height=42,
            width=120,
            font=ctk.CTkFont(family=self.theme["font_fallback"], size=13),
            **button_style(self.theme, "ghost"),
        )
        self.btn_back.pack(side="left")

        self.btn_restart = ctk.CTkButton(
            self.nav_frame,
            text=self.i18n.t("wizard.restart"),
            command=self.wizard.restart,
            corner_radius=10,
            height=42,
            width=140,
            font=ctk.CTkFont(family=self.theme["font_fallback"], size=13),
            **button_style(self.theme, "secondary"),
        )
        self.btn_restart.pack(side="left", padx=(8, 0))

        self.btn_next = ctk.CTkButton(
            self.nav_frame,
            text=self.i18n.t("wizard.next"),
            command=self.on_next,
            state="disabled",
            corner_radius=10,
            height=42,
            font=ctk.CTkFont(
                family=self.theme["font_fallback"], size=13, weight="bold"
            ),
            **button_style(self.theme, "primary"),
        )
        self.btn_next.pack(side="right")

    def enable_next(self):
        self.btn_next.configure(state="normal")

    def on_next(self):
        self.wizard.next_step()

    def apply_language(self):
        self.lbl_title.configure(text=self.i18n.t(self.title_key))
        self.lbl_description.configure(text=self.i18n.t(self.description_key))
        self.btn_back.configure(text=self.i18n.t("wizard.back"))
        self.btn_restart.configure(text=self.i18n.t("wizard.restart"))
        self.btn_next.configure(text=self.i18n.t("wizard.next"))

    def reset_state(self):
        self.btn_next.configure(state="disabled")


class WelcomeStep(WizardStep):
    def __init__(self, master, wizard):
        super().__init__(master, wizard, "wizard.welcome.title", "wizard.welcome.desc")
        self.build_content()
        self.enable_next()

    def build_content(self):
        self.lbl_content = ctk.CTkLabel(
            self.content_frame,
            text=self.i18n.t("wizard.welcome.content"),
            justify="left",
            anchor="w",
            font=ctk.CTkFont(family=self.theme["font_fallback"], size=22),
            text_color=self.theme["text"],
        )
        self.lbl_content.pack(anchor="w", pady=20)
        self.btn_next.configure(text=self.i18n.t("wizard.start"))

    def apply_language(self):
        super().apply_language()
        self.lbl_content.configure(text=self.i18n.t("wizard.welcome.content"))
        self.btn_next.configure(text=self.i18n.t("wizard.start"))

    def reset_state(self):
        self.enable_next()
        self.btn_next.configure(text=self.i18n.t("wizard.start"))


class VKAuthStep(WizardStep):
    def __init__(self, master, wizard):
        super().__init__(master, wizard, "wizard.vk.title", "wizard.vk.desc")
        self.build_content()

    def build_content(self):
        self.btn_login = ctk.CTkButton(
            self.content_frame,
            text=self.i18n.t("wizard.vk.login"),
            command=self.do_login,
            height=42,
            corner_radius=10,
            font=ctk.CTkFont(
                family=self.theme["font_fallback"], size=13, weight="bold"
            ),
            **button_style(self.theme, "primary"),
        )
        self.btn_login.pack(anchor="w", pady=(10, 16))

        self.lbl_status = ctk.CTkLabel(
            self.content_frame,
            text=self.i18n.t("wizard.vk.wait"),
            text_color=self.theme["muted"],
            font=ctk.CTkFont(family=self.theme["font_fallback"], size=13),
            anchor="w",
        )
        self.lbl_status.pack(fill="x")

    def do_login(self):
        self.lbl_status.configure(text=self.i18n.t("wizard.vk.launch"))
        self.btn_login.configure(state="disabled")
        self.wizard.controller.start_browser_and_login()

    def on_success(self):
        self.lbl_status.configure(
            text=self.i18n.t("wizard.vk.success"), text_color=self.theme["success"]
        )
        self.enable_next()

    def apply_language(self):
        super().apply_language()
        self.btn_login.configure(text=self.i18n.t("wizard.vk.login"))
        if self.btn_login.cget("state") == "normal":
            self.lbl_status.configure(
                text=self.i18n.t("wizard.vk.wait"), text_color=self.theme["muted"]
            )

    def reset_state(self):
        self.btn_login.configure(state="normal")
        self.lbl_status.configure(
            text=self.i18n.t("wizard.vk.wait"), text_color=self.theme["muted"]
        )
        self.btn_next.configure(state="disabled", text=self.i18n.t("wizard.next"))


class TelegramStep(WizardStep):
    def __init__(self, master, wizard):
        super().__init__(master, wizard, "wizard.tg.title", "wizard.tg.desc")
        self.help_visible = False
        self.build_content()

    def build_content(self):
        self.step_scroll = ctk.CTkScrollableFrame(
            self.content_frame,
            fg_color="transparent",
            corner_radius=0,
        )
        self.step_scroll.pack(fill="both", expand=True)

        self.strategy_codes = ["download_only", "download_upload", "direct_transfer"]
        self.mode_label_to_code = {}
        self.mode_code_to_label = {}

        self.lbl_mode = ctk.CTkLabel(
            self.step_scroll,
            text=self.i18n.t("wizard.tg.mode"),
            font=ctk.CTkFont(
                family=self.theme["font_fallback"], size=13, weight="bold"
            ),
            text_color=self.theme["text"],
            anchor="w",
        )
        self.lbl_mode.pack(fill="x", pady=(0, 4))

        self.lbl_mode_hint = ctk.CTkLabel(
            self.step_scroll,
            text=self.i18n.t("wizard.tg.mode.hint"),
            text_color=self.theme["muted"],
            font=ctk.CTkFont(family=self.theme["font_fallback"], size=12),
            justify="left",
            anchor="w",
            wraplength=620,
        )
        self.lbl_mode_hint.pack(fill="x", pady=(0, 8))

        self.seg_mode = ctk.CTkSegmentedButton(
            self.step_scroll,
            values=self._build_mode_values(),
            command=self.on_mode_change,
            selected_color=self.theme["accent"],
            selected_hover_color=self.theme["accent_hover"],
            unselected_color=self.theme["surface_alt"],
            unselected_hover_color=self.theme["nav_hover"],
            text_color=self.theme["text"],
        )
        self.seg_mode.pack(fill="x", pady=(0, 8))

        initial_mode = (
            self.wizard.controller.get_processing_strategy()
            if hasattr(self.wizard.controller, "get_processing_strategy")
            else "download_only"
        )
        self.seg_mode.set(
            self.mode_code_to_label.get(
                initial_mode, self.mode_code_to_label["download_only"]
            )
        )

        self.lbl_mode_state = ctk.CTkLabel(
            self.step_scroll,
            text="",
            text_color=self.theme["muted"],
            font=ctk.CTkFont(family=self.theme["font_fallback"], size=12),
            anchor="w",
            justify="left",
            wraplength=620,
        )
        self.lbl_mode_state.pack(fill="x", pady=(0, 10))

        self.entry_token = ctk.CTkEntry(
            self.step_scroll,
            placeholder_text=self.i18n.t("wizard.tg.token"),
            height=38,
            **entry_style(self.theme),
        )
        self.entry_token.pack(fill="x", pady=(6, 8))

        self.entry_chat_id = ctk.CTkEntry(
            self.step_scroll,
            placeholder_text=self.i18n.t("wizard.tg.chat"),
            height=38,
            **entry_style(self.theme),
        )
        self.entry_chat_id.pack(fill="x", pady=(0, 8))

        self.lbl_tip = ctk.CTkLabel(
            self.step_scroll,
            text=self.i18n.t("wizard.tg.tip"),
            text_color=self.theme["muted"],
            font=ctk.CTkFont(family=self.theme["font_fallback"], size=12),
            anchor="w",
            justify="left",
            wraplength=620,
        )
        self.lbl_tip.pack(fill="x", pady=(0, 14))

        btn_row = ctk.CTkFrame(self.step_scroll, fg_color="transparent")
        btn_row.pack(fill="x")

        self.btn_test = ctk.CTkButton(
            btn_row,
            text=self.i18n.t("telegram.test"),
            command=self.test_conn,
            corner_radius=10,
            height=40,
            **button_style(self.theme, "warning"),
        )
        self.btn_test.pack(side="left")

        self.btn_help = ctk.CTkButton(
            btn_row,
            text=self.i18n.t("wizard.tg.help.show"),
            command=self.toggle_help,
            corner_radius=10,
            height=40,
            width=140,
            **button_style(self.theme, "secondary"),
        )
        self.btn_help.pack(side="left", padx=(8, 0))

        self._build_help_panel()

        self.btn_skip = ctk.CTkButton(
            self.nav_frame,
            text=self.i18n.t("wizard.skip"),
            command=self.skip_telegram,
            corner_radius=10,
            height=40,
            **button_style(self.theme, "ghost"),
        )
        self.btn_skip.pack(side="left")

        self.entry_chat_id.bind(
            "<KeyRelease>", lambda _event: self._sync_chat_id_check()
        )
        self._apply_mode_state()

    def _build_mode_values(self):
        self.mode_label_to_code = {}
        self.mode_code_to_label = {}
        labels = []
        for code in self.strategy_codes:
            label = self.i18n.t(f"strategy.{code}")
            self.mode_label_to_code[label] = code
            self.mode_code_to_label[code] = label
            labels.append(label)
        return labels

    def _current_mode(self):
        return self.mode_label_to_code.get(self.seg_mode.get(), "download_only")

    def on_mode_change(self, _value):
        mode = self._current_mode()
        if hasattr(self.wizard.controller, "set_processing_strategy"):
            self.wizard.controller.set_processing_strategy(mode)
        self._apply_mode_state()

    def _apply_mode_state(self):
        mode = self._current_mode()
        needs_tg = mode in ["download_upload", "direct_transfer"]
        state = "normal" if needs_tg else "disabled"

        self.entry_token.configure(state=state)
        self.entry_chat_id.configure(state=state)
        self.btn_test.configure(state=state)

        if needs_tg:
            self.lbl_mode_state.configure(
                text=self.i18n.t("wizard.tg.mode.required"),
                text_color=self.theme["warning"],
            )
            self.btn_next.configure(state="disabled", text=self.i18n.t("wizard.next"))
        else:
            self.lbl_mode_state.configure(
                text=self.i18n.t("wizard.tg.mode.local"),
                text_color=self.theme["success"],
            )
            self.enable_next()
            self.btn_next.configure(text=self.i18n.t("wizard.next"))

    def skip_telegram(self):
        self.seg_mode.set(self.mode_code_to_label["download_only"])
        self.on_mode_change(self.seg_mode.get())
        self.on_next()

    def _build_help_panel(self):
        self.help_panel = ctk.CTkFrame(
            self.step_scroll,
            fg_color=self.theme["surface"],
            border_width=1,
            border_color=self.theme["border"],
            corner_radius=12,
        )

        self.lbl_help_title = ctk.CTkLabel(
            self.help_panel,
            text=self.i18n.t("wizard.tg.help.title"),
            font=ctk.CTkFont(
                family=self.theme["font_fallback"], size=14, weight="bold"
            ),
            text_color=self.theme["text"],
            anchor="w",
        )
        self.lbl_help_title.pack(fill="x", padx=12, pady=(10, 2))

        self.lbl_help_subtitle = ctk.CTkLabel(
            self.help_panel,
            text=self.i18n.t("wizard.tg.help.subtitle"),
            font=ctk.CTkFont(family=self.theme["font_fallback"], size=12),
            text_color=self.theme["muted"],
            anchor="w",
            justify="left",
            wraplength=600,
        )
        self.lbl_help_subtitle.pack(fill="x", padx=12, pady=(0, 8))

        links_row = ctk.CTkFrame(self.help_panel, fg_color="transparent")
        links_row.pack(fill="x", padx=12, pady=(0, 8))

        self.btn_open_botfather = ctk.CTkButton(
            links_row,
            text=self.i18n.t("wizard.tg.open.botfather"),
            command=lambda: self._open_link("https://t.me/BotFather"),
            corner_radius=8,
            height=32,
            **button_style(self.theme, "secondary"),
        )
        self.btn_open_botfather.pack(side="left")

        self.btn_open_getmyid = ctk.CTkButton(
            links_row,
            text=self.i18n.t("wizard.tg.open.getmyid"),
            command=lambda: self._open_link("https://t.me/getmyid_bot"),
            corner_radius=8,
            height=32,
            **button_style(self.theme, "secondary"),
        )
        self.btn_open_getmyid.pack(side="left", padx=(8, 0))

        self.stage1_title, self.stage1_steps = self._create_stage_card(
            self.help_panel,
            "wizard.tg.stage1",
            [
                "wizard.tg.stage1.step1",
                "wizard.tg.stage1.step2",
                "wizard.tg.stage1.step3",
            ],
        )
        self.stage2_title, self.stage2_steps = self._create_stage_card(
            self.help_panel,
            "wizard.tg.stage2",
            [
                "wizard.tg.stage2.step1",
                "wizard.tg.stage2.step2",
                "wizard.tg.stage2.step3",
            ],
        )
        self.stage3_title, self.stage3_steps = self._create_stage_card(
            self.help_panel,
            "wizard.tg.stage3",
            [
                "wizard.tg.stage3.step1",
                "wizard.tg.stage3.step2",
                "wizard.tg.stage3.step3",
            ],
        )

        checklist = ctk.CTkFrame(
            self.help_panel, fg_color=self.theme["surface_alt"], corner_radius=10
        )
        checklist.pack(fill="x", padx=12, pady=(4, 12))

        self.lbl_checklist = ctk.CTkLabel(
            checklist,
            text=self.i18n.t("wizard.tg.checklist"),
            font=ctk.CTkFont(
                family=self.theme["font_fallback"], size=12, weight="bold"
            ),
            text_color=self.theme["muted"],
            anchor="w",
        )
        self.lbl_checklist.pack(fill="x", padx=10, pady=(8, 2))

        self.chk_bot_var = ctk.BooleanVar(value=False)
        self.chk_group_var = ctk.BooleanVar(value=False)
        self.chk_admin_var = ctk.BooleanVar(value=False)
        self.chk_chat_var = ctk.BooleanVar(value=False)

        self.chk_bot = ctk.CTkCheckBox(
            checklist,
            text=self.i18n.t("wizard.tg.check.bot"),
            variable=self.chk_bot_var,
            command=self._update_help_progress,
            **checkbox_style(self.theme),
        )
        self.chk_bot.pack(anchor="w", padx=10, pady=2)
        self.chk_group = ctk.CTkCheckBox(
            checklist,
            text=self.i18n.t("wizard.tg.check.group"),
            variable=self.chk_group_var,
            command=self._update_help_progress,
            **checkbox_style(self.theme),
        )
        self.chk_group.pack(anchor="w", padx=10, pady=2)
        self.chk_admin = ctk.CTkCheckBox(
            checklist,
            text=self.i18n.t("wizard.tg.check.admin"),
            variable=self.chk_admin_var,
            command=self._update_help_progress,
            **checkbox_style(self.theme),
        )
        self.chk_admin.pack(anchor="w", padx=10, pady=2)
        self.chk_chat = ctk.CTkCheckBox(
            checklist,
            text=self.i18n.t("wizard.tg.check.chat"),
            variable=self.chk_chat_var,
            command=self._update_help_progress,
            **checkbox_style(self.theme),
        )
        self.chk_chat.pack(anchor="w", padx=10, pady=2)

        self.lbl_progress = ctk.CTkLabel(
            checklist,
            text="",
            font=ctk.CTkFont(
                family=self.theme["font_fallback"], size=12, weight="bold"
            ),
            text_color=self.theme["accent"],
            anchor="w",
        )
        self.lbl_progress.pack(fill="x", padx=10, pady=(4, 8))
        self._update_help_progress()

    def _create_stage_card(self, parent, title_key, step_keys):
        card = ctk.CTkFrame(
            parent, fg_color=self.theme["surface_alt"], corner_radius=10
        )
        card.pack(fill="x", padx=12, pady=(0, 8))

        title = ctk.CTkLabel(
            card,
            text=self.i18n.t(title_key),
            font=ctk.CTkFont(
                family=self.theme["font_fallback"], size=12, weight="bold"
            ),
            text_color=self.theme["text"],
            anchor="w",
        )
        title.pack(fill="x", padx=10, pady=(8, 2))

        step_labels = []
        for step_key in step_keys:
            step = ctk.CTkLabel(
                card,
                text=f"• {self.i18n.t(step_key)}",
                font=ctk.CTkFont(family=self.theme["font_fallback"], size=12),
                text_color=self.theme["muted"],
                anchor="w",
                justify="left",
                wraplength=600,
            )
            step.pack(fill="x", padx=10, pady=(0, 2))
            step_labels.append((step, step_key))

        return (title, title_key), step_labels

    def _open_link(self, url):
        try:
            webbrowser.open(url)
        except Exception as exc:
            logger.warning(f"Не удалось открыть ссылку {url}: {exc}")

    def _sync_chat_id_check(self):
        value = self.entry_chat_id.get().strip()
        self.chk_chat_var.set(bool(value and value.startswith("-")))
        self._update_help_progress()

    def _update_help_progress(self):
        done = sum(
            [
                bool(self.chk_bot_var.get()),
                bool(self.chk_group_var.get()),
                bool(self.chk_admin_var.get()),
                bool(self.chk_chat_var.get()),
            ]
        )
        self.lbl_progress.configure(
            text=self.i18n.t("wizard.tg.progress", done=done, total=4)
        )

    def toggle_help(self):
        self.help_visible = not self.help_visible
        if self.help_visible:
            self.help_panel.pack(fill="x", pady=(10, 8))
            self.btn_help.configure(text=self.i18n.t("wizard.tg.help.hide"))
        else:
            self.help_panel.pack_forget()
            self.btn_help.configure(text=self.i18n.t("wizard.tg.help.show"))

    def test_conn(self):
        if self._current_mode() == "download_only":
            self.enable_next()
            self.btn_next.configure(text=self.i18n.t("wizard.next"))
            return

        token = self.entry_token.get()
        chat_id = self.entry_chat_id.get()

        if not token or not chat_id:
            logger.warning("Token or ChatID missing")
            return

        self.wizard.controller.settings_manager.set("tg_bot_token", token)
        self.wizard.controller.settings_manager.set("tg_chat_id", chat_id)
        self.wizard.controller.save_tg_settings(token, chat_id)

        success, msg = self.wizard.controller.test_tg_connection()
        if success:
            self.enable_next()
            self.btn_next.configure(text=self.i18n.t("wizard.next"))
        else:
            logger.error(f"TG Test failed: {msg}")

    def apply_language(self):
        super().apply_language()
        selected_mode = self._current_mode()
        mode_values = self._build_mode_values()
        self.lbl_mode.configure(text=self.i18n.t("wizard.tg.mode"))
        self.lbl_mode_hint.configure(text=self.i18n.t("wizard.tg.mode.hint"))
        self.seg_mode.configure(values=mode_values)
        self.seg_mode.set(
            self.mode_code_to_label.get(
                selected_mode, self.mode_code_to_label["download_only"]
            )
        )
        self.entry_token.configure(placeholder_text=self.i18n.t("wizard.tg.token"))
        self.entry_chat_id.configure(placeholder_text=self.i18n.t("wizard.tg.chat"))
        self.lbl_tip.configure(text=self.i18n.t("wizard.tg.tip"))
        self.btn_test.configure(text=self.i18n.t("telegram.test"))
        self.btn_help.configure(
            text=(
                self.i18n.t("wizard.tg.help.hide")
                if self.help_visible
                else self.i18n.t("wizard.tg.help.show")
            )
        )
        self.lbl_help_title.configure(text=self.i18n.t("wizard.tg.help.title"))
        self.lbl_help_subtitle.configure(text=self.i18n.t("wizard.tg.help.subtitle"))
        self.btn_open_botfather.configure(text=self.i18n.t("wizard.tg.open.botfather"))
        self.btn_open_getmyid.configure(text=self.i18n.t("wizard.tg.open.getmyid"))

        self.stage1_title[0].configure(text=self.i18n.t(self.stage1_title[1]))
        self.stage2_title[0].configure(text=self.i18n.t(self.stage2_title[1]))
        self.stage3_title[0].configure(text=self.i18n.t(self.stage3_title[1]))
        for label, key in self.stage1_steps + self.stage2_steps + self.stage3_steps:
            label.configure(text=f"• {self.i18n.t(key)}")

        self.lbl_checklist.configure(text=self.i18n.t("wizard.tg.checklist"))
        self.chk_bot.configure(text=self.i18n.t("wizard.tg.check.bot"))
        self.chk_group.configure(text=self.i18n.t("wizard.tg.check.group"))
        self.chk_admin.configure(text=self.i18n.t("wizard.tg.check.admin"))
        self.chk_chat.configure(text=self.i18n.t("wizard.tg.check.chat"))
        self._update_help_progress()
        self.btn_skip.configure(text=self.i18n.t("wizard.skip"))
        self._apply_mode_state()

    def reset_state(self):
        current_mode = (
            self.wizard.controller.get_processing_strategy()
            if hasattr(self.wizard.controller, "get_processing_strategy")
            else "download_only"
        )
        self.seg_mode.set(
            self.mode_code_to_label.get(
                current_mode, self.mode_code_to_label["download_only"]
            )
        )
        self._apply_mode_state()
        self.help_visible = False
        self.help_panel.pack_forget()
        self.btn_help.configure(text=self.i18n.t("wizard.tg.help.show"))
        self.chk_bot_var.set(False)
        self.chk_group_var.set(False)
        self.chk_admin_var.set(False)
        self._sync_chat_id_check()


class StorageStep(WizardStep):
    def __init__(self, master, wizard):
        super().__init__(master, wizard, "wizard.storage.title", "wizard.storage.desc")
        self.build_content()

    def build_content(self):
        self.entry_path = ctk.CTkEntry(
            self.content_frame,
            placeholder_text=self.i18n.t("wizard.storage.path"),
            height=38,
            **entry_style(self.theme),
        )
        self.entry_path.pack(fill="x", pady=(12, 10))
        self.entry_path.insert(0, "data/downloads")

        self.btn_browse = ctk.CTkButton(
            self.content_frame,
            text=self.i18n.t("wizard.storage.browse"),
            command=self.browse,
            corner_radius=10,
            height=40,
            **button_style(self.theme, "secondary"),
        )
        self.btn_browse.pack(anchor="w")

        self.enable_next()
        self.btn_next.configure(text=self.i18n.t("wizard.finish"))

    def browse(self):
        path = filedialog.askdirectory()
        if path:
            self.entry_path.delete(0, "end")
            self.entry_path.insert(0, path)

    def on_next(self):
        dl_path = self.entry_path.get()
        self.wizard.controller.settings_manager.set("download_path", dl_path)
        super().on_next()

    def apply_language(self):
        super().apply_language()
        self.entry_path.configure(placeholder_text=self.i18n.t("wizard.storage.path"))
        self.btn_browse.configure(text=self.i18n.t("wizard.storage.browse"))
        self.btn_next.configure(text=self.i18n.t("wizard.finish"))

    def reset_state(self):
        self.enable_next()
        self.btn_next.configure(text=self.i18n.t("wizard.finish"))


class SetupWizard(ctk.CTk):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.theme = get_theme()
        self.i18n = I18n(
            self.controller.get_language()
            if hasattr(self.controller, "get_language")
            else "ru"
        )

        self.title(self.i18n.t("wizard.title"))
        self.geometry("760x560")
        self.resizable(False, False)
        self.configure(fg_color=self.theme["bg"])

        center_x = self.winfo_screenwidth() // 2 - 380
        center_y = self.winfo_screenheight() // 2 - 280
        self.geometry(f"+{center_x}+{center_y}")

        self.original_on_log = self.controller.on_log
        self.original_on_login_success = self.controller.on_login_success

        self._ui_events = Queue()
        self._after_ids = set()
        self._is_closing = False
        self.controller.on_log = lambda msg: self._ui_events.put(("log", msg))
        self.controller.on_login_success = lambda: self._ui_events.put(
            ("login_success", None)
        )

        self.step = 1

        self.container = ctk.CTkFrame(
            self,
            fg_color=self.theme["panel"],
            corner_radius=18,
            border_width=1,
            border_color=self.theme["border"],
        )
        self.container.pack(fill="both", expand=True, padx=18, pady=18)

        top_row = ctk.CTkFrame(self.container, fg_color="transparent")
        top_row.pack(fill="x", padx=14, pady=(14, 0))

        self.lbl_progress = ctk.CTkLabel(
            top_row,
            text="",
            text_color=self.theme["muted"],
            font=ui_font(self.theme, 12, "bold", alt=True),
        )
        self.lbl_progress.pack(side="left")

        self.lang_switch = ctk.CTkFrame(
            top_row, fg_color=self.theme["surface"], corner_radius=10
        )
        self.lang_switch.pack(side="right")

        self.btn_lang_ru = ctk.CTkButton(
            self.lang_switch,
            text="RU",
            width=52,
            height=30,
            corner_radius=8,
            font=ui_font(self.theme, 12, "bold"),
            command=lambda: self.on_language_change("RU"),
        )
        self.btn_lang_ru.pack(side="left", padx=(4, 2), pady=4)

        self.btn_lang_en = ctk.CTkButton(
            self.lang_switch,
            text="EN",
            width=52,
            height=30,
            corner_radius=8,
            font=ui_font(self.theme, 12, "bold"),
            command=lambda: self.on_language_change("EN"),
        )
        self.btn_lang_en.pack(side="left", padx=(2, 4), pady=4)
        self._set_language_buttons("ru" if self.i18n.language == "ru" else "en")

        self.steps_host = ctk.CTkFrame(self.container, fg_color="transparent")
        self.steps_host.pack(fill="both", expand=True, padx=14, pady=(6, 14))

        self.steps_map = {
            1: WelcomeStep(self.steps_host, self),
            2: VKAuthStep(self.steps_host, self),
            3: TelegramStep(self.steps_host, self),
            4: StorageStep(self.steps_host, self),
        }

        self.show_step(1)
        self.apply_language()
        self.process_ui_events()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def _window_alive(self):
        try:
            return bool(self.winfo_exists())
        except TclError:
            return False

    def _schedule_after(self, delay_ms, callback):
        if self._is_closing or not self._window_alive():
            return None

        after_id = None

        def _wrapped():
            if after_id is not None:
                self._after_ids.discard(after_id)
            if self._is_closing or not self._window_alive():
                return
            callback()

        try:
            after_id = self.after(delay_ms, _wrapped)
            self._after_ids.add(after_id)
            return after_id
        except TclError:
            return None

    def _cancel_after_callbacks(self):
        for after_id in list(self._after_ids):
            try:
                self.after_cancel(after_id)
            except TclError:
                pass
            finally:
                self._after_ids.discard(after_id)

    def _render_progress(self):
        self.lbl_progress.configure(
            text=self.i18n.t(
                "wizard.progress", current=self.step, total=len(self.steps_map)
            )
        )

    def log_handler(self, msg):
        print(f"[Wizard Log] {msg}")

    def on_login_success_handler(self):
        if 2 in self.steps_map:
            self.steps_map[2].on_success()

    def next_step(self):
        if self.step < len(self.steps_map):
            self.step += 1
            self.show_step(self.step)
        else:
            self.finish()

    def prev_step(self):
        if self.step > 1:
            self.step -= 1
            self.show_step(self.step)

    def restart(self):
        for frame in self.steps_map.values():
            if hasattr(frame, "reset_state"):
                frame.reset_state()
        self.show_step(1)

    def show_step(self, step_num):
        self.step = step_num
        self._render_progress()
        for frame in self.steps_map.values():
            frame.pack_forget()
        current_frame = self.steps_map[step_num]
        current_frame.pack(fill="both", expand=True)
        if hasattr(current_frame, "btn_back"):
            if step_num == 1:
                current_frame.btn_back.pack_forget()
                current_frame.btn_restart.pack_forget()
            else:
                if not current_frame.btn_back.winfo_manager():
                    current_frame.btn_back.pack(side="left")
                if not current_frame.btn_restart.winfo_manager():
                    current_frame.btn_restart.pack(side="left", padx=(8, 0))
                current_frame.btn_back.configure(state="normal")

    def _set_language_buttons(self, language):
        active_style = button_style(self.theme, "primary")
        idle_style = button_style(self.theme, "secondary")
        if language == "ru":
            self.btn_lang_ru.configure(**active_style)
            self.btn_lang_en.configure(**idle_style)
        else:
            self.btn_lang_ru.configure(**idle_style)
            self.btn_lang_en.configure(**active_style)

    def on_language_change(self, value):
        language = "ru" if value == "RU" else "en"
        if language == self.i18n.language:
            return
        self.i18n.set_language(language)
        self._set_language_buttons(language)
        if hasattr(self.controller, "set_language"):
            self.controller.set_language(language)
        self.apply_language()

    def apply_language(self):
        self.title(self.i18n.t("wizard.title"))
        self._set_language_buttons(self.i18n.language)
        self._render_progress()
        for frame in self.steps_map.values():
            frame.apply_language()

    def finish(self):
        self.controller.settings_manager.set("setup_completed", True)

        self.controller.on_log = self.original_on_log
        self.controller.on_login_success = self.original_on_login_success

        self._is_closing = True
        self._cancel_after_callbacks()
        if self._window_alive():
            self.destroy()

    def on_close(self):

        self.controller.on_log = self.original_on_log
        self.controller.on_login_success = self.original_on_login_success

        self._is_closing = True
        self._cancel_after_callbacks()
        if self._window_alive():
            self.destroy()

    def process_ui_events(self):
        if self._is_closing or not self._window_alive():
            return

        try:
            while True:
                event, payload = self._ui_events.get_nowait()
                if event == "log":
                    self.log_handler(payload)
                elif event == "login_success":
                    self.on_login_success_handler()
        except Empty:
            pass

        self._schedule_after(120, self.process_ui_events)
