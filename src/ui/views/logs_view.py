import customtkinter as ctk
import datetime

from src.ui.components.primitives import ConsolePanel, EmptyState, StatusBadge, Surface
from src.ui.design_system import button_style, ui_font


class LogsView(ctk.CTkFrame):
    def __init__(self, master, i18n, theme):
        super().__init__(master, fg_color="transparent")
        self.i18n = i18n
        self.theme = theme
        self.entry_count = 0

        self.meta = Surface(self, self.theme, variant="surface")
        self.meta.pack(fill="x", padx=0, pady=(0, 10))

        self.stream_badge = StatusBadge(
            self.meta,
            self.theme,
            self.i18n.t("logs.idle"),
            tone="neutral",
        )
        self.stream_badge.pack(side="left", padx=14, pady=12)

        self.lbl_meta = ctk.CTkLabel(
            self.meta,
            text=self._meta_text(),
            text_color=self.theme["muted"],
            font=ui_font(self.theme, 12, alt=True),
            anchor="w",
        )
        self.lbl_meta.pack(side="left", padx=(0, 12), pady=12)

        self.btn_clear = ctk.CTkButton(
            self.meta,
            text=self.i18n.t("logs.clear"),
            width=110,
            height=34,
            command=self.clear,
            font=ui_font(self.theme, 12, "bold"),
            **button_style(self.theme, "secondary"),
        )
        self.btn_clear.pack(side="right", padx=14, pady=10)

        self.console_shell = Surface(self, self.theme, variant="panel")
        self.console_shell.pack(fill="both", expand=True, padx=0, pady=0)

        self.empty_state = EmptyState(
            self.console_shell,
            self.theme,
            self.i18n.t("logs.empty.title"),
            self.i18n.t("logs.empty.body"),
        )
        self.empty_state.pack(fill="x", padx=14, pady=(14, 0))

        self.console = ConsolePanel(self.console_shell, self.theme)
        self.console.pack(fill="both", expand=True, padx=14, pady=14)
        self.textbox = self.console.textbox

    def apply_language(self):
        self.btn_clear.configure(text=self.i18n.t("logs.clear"))
        self.empty_state.configure_content(
            self.i18n.t("logs.empty.title"),
            self.i18n.t("logs.empty.body"),
        )
        self._update_meta_state()

    def clear(self):
        self.textbox.configure(state="normal")
        self.textbox.delete("1.0", "end")
        self.textbox.configure(state="disabled")
        self.entry_count = 0
        self._update_meta_state()
        if not self.empty_state.winfo_manager():
            self.empty_state.pack(fill="x", padx=14, pady=(14, 0))

    def append(self, text):
        self.append_many([text])

    def append_many(self, lines):
        if not lines:
            return
        if self.empty_state.winfo_manager():
            self.empty_state.pack_forget()
        self.textbox.configure(state="normal")
        for text in lines:
            ts = datetime.datetime.now().strftime("%H:%M:%S")
            self.textbox.insert("end", f"[{ts}] {text}\n")
            self.entry_count += 1
        self.textbox.see("end")
        self.textbox.configure(state="disabled")
        self._update_meta_state()

    def _meta_text(self):
        return self.i18n.t("logs.meta", count=self.entry_count)

    def _update_meta_state(self):
        active = self.entry_count > 0
        self.lbl_meta.configure(text=self._meta_text())
        self.stream_badge.configure_tone(
            "info" if active else "neutral",
            self.i18n.t("logs.live") if active else self.i18n.t("logs.idle"),
        )
