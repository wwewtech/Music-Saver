import customtkinter as ctk
import datetime
from src.ui.design_system import ui_font, button_style


class LogsView(ctk.CTkFrame):
    def __init__(self, master, i18n, theme):
        super().__init__(master, fg_color="transparent")
        self.i18n = i18n
        self.theme = theme

        self.lbl_title = ctk.CTkLabel(
            self,
            text=self.i18n.t("logs.title"),
            font=ui_font(self.theme, 24, "bold"),
            text_color=self.theme["text"],
            anchor="w",
        )
        self.lbl_title.pack(fill="x", padx=8, pady=(8, 0))

        topbar = ctk.CTkFrame(
            self,
            fg_color="transparent",
        )
        topbar.pack(fill="x", padx=8, pady=(0, 8))

        self.lbl_subtitle = ctk.CTkLabel(
            topbar,
            text=self.i18n.t("logs.subtitle"),
            text_color=self.theme["muted"],
            font=ui_font(self.theme, 12, alt=True),
            anchor="w",
        )
        self.lbl_subtitle.pack(side="left")

        self.btn_clear = ctk.CTkButton(
            topbar,
            text=self.i18n.t("logs.clear"),
            width=100,
            height=34,
            command=self.clear,
            **button_style(self.theme, "secondary"),
        )
        self.btn_clear.pack(side="right")

        self.textbox = ctk.CTkTextbox(
            self,
            fg_color=self.theme["panel"],
            border_width=1,
            border_color=self.theme["border"],
            text_color=self.theme["text"],
            font=ui_font(self.theme, 13, alt=True),
            corner_radius=12,
        )
        self.textbox.pack(fill="both", expand=True, padx=6, pady=(0, 2))
        self.textbox.configure(state="disabled")

    def apply_language(self):
        self.lbl_title.configure(text=self.i18n.t("logs.title"))
        self.lbl_subtitle.configure(text=self.i18n.t("logs.subtitle"))
        self.btn_clear.configure(text=self.i18n.t("logs.clear"))

    def clear(self):
        self.textbox.configure(state="normal")
        self.textbox.delete("1.0", "end")
        self.textbox.configure(state="disabled")

    def append(self, text):
        self.append_many([text])

    def append_many(self, lines):
        if not lines:
            return
        self.textbox.configure(state="normal")
        for text in lines:
            ts = datetime.datetime.now().strftime("%H:%M:%S")
            self.textbox.insert("end", f"[{ts}] {text}\n")
        self.textbox.see("end")
        self.textbox.configure(state="disabled")
