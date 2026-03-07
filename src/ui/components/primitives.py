import customtkinter as ctk

from src.ui.design_system import surface_style, ui_font

_resize_locked = False
_pending_wrap_widgets = []


def set_resize_lock(locked):
    global _resize_locked
    _resize_locked = locked


def flush_pending_wraps():
    global _pending_wrap_widgets
    jobs = _pending_wrap_widgets
    _pending_wrap_widgets = []
    for fn in jobs:
        fn()


def bind_auto_wrap(widget, label, horizontal_padding=0, min_wrap=120):
    def _apply_wrap():
        setattr(label, "_auto_wrap_after_id", None)
        if _resize_locked:
            if _apply_wrap not in _pending_wrap_widgets:
                _pending_wrap_widgets.append(_apply_wrap)
            return
        try:
            if not widget.winfo_ismapped():
                return
            width = widget.winfo_width() - horizontal_padding
        except Exception:
            return

        if width > 1:
            wraplength = max(width, min_wrap)
            last = getattr(label, "_auto_wrap_last_wrap", None)
            if last is not None and abs(last - wraplength) < 50:
                return
            label.configure(wraplength=wraplength)
            label._auto_wrap_last_wrap = wraplength

    def _update(_event=None):
        if _resize_locked:
            return
        after_id = getattr(label, "_auto_wrap_after_id", None)
        if after_id is not None:
            try:
                widget.after_cancel(after_id)
            except Exception:
                pass

        try:
            label._auto_wrap_after_id = widget.after(150, _apply_wrap)
        except Exception:
            pass

    widget.bind("<Configure>", _update, add="+")
    widget.after(0, _update)


class Surface(ctk.CTkFrame):
    def __init__(self, master, theme, variant="surface", **kwargs):
        style = surface_style(theme, variant)
        kwargs.setdefault("fg_color", style["fg_color"])
        kwargs.setdefault("border_color", style["border_color"])
        kwargs.setdefault("corner_radius", style["corner_radius"])
        kwargs.setdefault("border_width", 1)
        super().__init__(
            master,
            **kwargs,
        )
        self.theme = theme


class StatusBadge(ctk.CTkFrame):
    def __init__(self, master, theme, text, tone="neutral", **kwargs):
        super().__init__(
            master,
            fg_color=theme["surface_emphasis"],
            corner_radius=999,
            border_width=1,
            border_color=theme["border_soft"],
            **kwargs,
        )
        self.theme = theme
        self.label = ctk.CTkLabel(
            self,
            text=text,
            font=ui_font(theme, 11, "bold", alt=True),
            anchor="center",
        )
        self.label.pack(padx=10, pady=4)
        self.configure_tone(tone)

    _tone_map = None

    def configure_tone(self, tone="neutral", text=None):
        if StatusBadge._tone_map is None:
            StatusBadge._tone_map = {}
        theme_id = id(self.theme)
        if theme_id not in StatusBadge._tone_map:
            StatusBadge._tone_map[theme_id] = {
                "neutral": {
                    "fg": self.theme["surface_emphasis"],
                    "border": self.theme["border_soft"],
                    "text": self.theme["text_soft"],
                },
                "success": {
                    "fg": "#102017",
                    "border": "#1e5c39",
                    "text": self.theme["success"],
                },
                "warning": {
                    "fg": "#24180b",
                    "border": "#6d4912",
                    "text": self.theme["warning"],
                },
                "danger": {
                    "fg": "#261214",
                    "border": "#6d2a2d",
                    "text": self.theme["danger"],
                },
                "info": {
                    "fg": "#101826",
                    "border": "#24456f",
                    "text": self.theme["info"],
                },
            }
        colors = StatusBadge._tone_map[theme_id].get(tone, StatusBadge._tone_map[theme_id]["neutral"])
        next_text = text or self.label.cget("text")
        if self.label.cget("text") != next_text or self.label.cget("text_color") != colors["text"]:
            self.label.configure(text=next_text, text_color=colors["text"])
        try:
            current_fg = self.cget("fg_color")
            current_border = self.cget("border_color")
        except Exception:
            current_fg = current_border = None
        if current_fg != colors["fg"] or current_border != colors["border"]:
            self.configure(fg_color=colors["fg"], border_color=colors["border"])


class SectionHeader(ctk.CTkFrame):
    def __init__(self, master, theme, title, description=None, eyebrow=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.theme = theme
        self.grid_columnconfigure(0, weight=1)

        self.eyebrow = None
        if eyebrow:
            self.eyebrow = ctk.CTkLabel(
                self,
                text=eyebrow,
                font=ui_font(theme, 11, "bold", alt=True),
                text_color=theme["muted"],
                anchor="w",
            )
            self.eyebrow.grid(row=0, column=0, sticky="ew")

        title_row = 1 if eyebrow else 0
        self.title = ctk.CTkLabel(
            self,
            text=title,
            font=ui_font(theme, 18, "bold"),
            text_color=theme["text"],
            anchor="w",
        )
        self.title.grid(row=title_row, column=0, sticky="ew")

        self.description = None
        if description is not None:
            self.description = ctk.CTkLabel(
                self,
                text=description,
                font=ui_font(theme, 12, alt=True),
                text_color=theme["muted"],
                justify="left",
                anchor="w",
                wraplength=900,
            )
            self.description.grid(row=title_row + 1, column=0, sticky="ew", pady=(4, 0))
            bind_auto_wrap(self, self.description, horizontal_padding=8, min_wrap=180)

    def configure_content(self, title=None, description=None, eyebrow=None):
        if title is not None and self.title.cget("text") != title:
            self.title.configure(text=title)
        if self.description and description is not None and self.description.cget("text") != description:
            self.description.configure(text=description)
        if self.eyebrow and eyebrow is not None and self.eyebrow.cget("text") != eyebrow:
            self.eyebrow.configure(text=eyebrow)


class MetricTile(Surface):
    def __init__(self, master, theme, label, value, accent=False, description=None, **kwargs):
        super().__init__(master, theme, variant="surface", **kwargs)
        value_color = theme["text"] if accent else theme["text_soft"]
        value_size = 40 if accent else 26

        self.value_label = ctk.CTkLabel(
            self,
            text=value,
            font=ui_font(theme, value_size, "bold", mono=not accent),
            text_color=value_color,
            anchor="w",
        )
        self.value_label.pack(anchor="w", padx=18, pady=(16, 0))

        self.title_label = ctk.CTkLabel(
            self,
            text=label,
            font=ui_font(theme, 12, "bold", alt=True),
            text_color=theme["muted"],
            anchor="w",
        )
        self.title_label.pack(anchor="w", padx=18, pady=(6, 0))

        self.description_label = ctk.CTkLabel(
            self,
            text=description or "",
            font=ui_font(theme, 12, alt=True),
            text_color=theme["muted_soft"],
            anchor="w",
            justify="left",
            wraplength=320,
        )
        self.description_label.pack(anchor="w", padx=18, pady=(4, 16))
        bind_auto_wrap(self, self.description_label, horizontal_padding=48, min_wrap=180)
        if not description:
            self.description_label.pack_forget()

    def set_value(self, value):
        if self.value_label.cget("text") != value:
            self.value_label.configure(text=value)

    def set_label(self, text):
        if self.title_label.cget("text") != text:
            self.title_label.configure(text=text)

    def set_description(self, text):
        if text:
            if not self.description_label.winfo_manager():
                self.description_label.pack(anchor="w", padx=18, pady=(4, 16))
            if self.description_label.cget("text") != text:
                self.description_label.configure(text=text)
        elif self.description_label.winfo_manager():
            self.description_label.pack_forget()


class EmptyState(Surface):
    def __init__(self, master, theme, title, body, **kwargs):
        super().__init__(master, theme, variant="soft", **kwargs)
        self.title_label = ctk.CTkLabel(
            self,
            text=title,
            font=ui_font(theme, 14, "bold"),
            text_color=theme["text"],
            anchor="w",
        )
        self.title_label.pack(anchor="w", padx=18, pady=(16, 4))
        self.body_label = ctk.CTkLabel(
            self,
            text=body,
            font=ui_font(theme, 12, alt=True),
            text_color=theme["muted"],
            justify="left",
            anchor="w",
            wraplength=520,
        )
        self.body_label.pack(anchor="w", padx=18, pady=(0, 16))
        bind_auto_wrap(self, self.body_label, horizontal_padding=48, min_wrap=180)

    def configure_content(self, title, body):
        if self.title_label.cget("text") != title:
            self.title_label.configure(text=title)
        if self.body_label.cget("text") != body:
            self.body_label.configure(text=body)


class ConsolePanel(Surface):
    def __init__(self, master, theme, **kwargs):
        super().__init__(master, theme, variant="panel", **kwargs)
        self.textbox = ctk.CTkTextbox(
            self,
            fg_color=theme["panel"],
            border_width=0,
            text_color=theme["text_soft"],
            font=ui_font(theme, 12, mono=True),
            corner_radius=0,
            wrap="word",
        )
        self.textbox.pack(fill="both", expand=True, padx=2, pady=2)
        self.textbox.configure(state="disabled")