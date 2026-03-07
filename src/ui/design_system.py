import customtkinter as ctk


def get_theme():
    return {
        "font": "Segoe UI Variable Text",
        "font_alt": "Segoe UI",
        "font_fallback": "Segoe UI",
        "font_mono": "Cascadia Code",
        "page_bg": "#09090b",
        "shell_bg": "#0c0c0f",
        "panel": "#111113",
        "surface": "#16161a",
        "surface_alt": "#1d1d22",
        "surface_soft": "#141419",
        "surface_emphasis": "#202028",
        "border": "#26262e",
        "border_strong": "#343441",
        "border_soft": "#1f1f27",
        "text": "#fafafa",
        "text_soft": "#d4d4db",
        "muted": "#9f9faa",
        "muted_soft": "#7f7f89",
        "accent": "#f4f4f5",
        "accent_hover": "#ffffff",
        "text_on_accent": "#09090b",
        "success": "#35c97a",
        "success_hover": "#45d98a",
        "warning": "#f59e0b",
        "warning_hover": "#ffb547",
        "danger": "#f87171",
        "danger_hover": "#fb8b8b",
        "info": "#60a5fa",
        "info_hover": "#93c5fd",
        "focus": "#fafafa",
        "input_bg": "#101014",
        "card": "#16161a",
        "bg": "#09090b",
        "nav_idle": "#111113",
        "nav_hover": "#1d1d22",
        "nav_active_bg": "#202028",
        "nav_active_border": "#3b3b47",
        "radius_sm": 10,
        "radius_md": 14,
        "radius_lg": 18,
        "control_height_sm": 32,
        "control_height_md": 40,
        "control_height_lg": 48,
    }


_font_cache = {}


def ui_font(theme, size, weight="normal", alt=False, mono=False):
    if mono:
        family = theme["font_mono"]
    else:
        family = theme["font_alt"] if alt else theme["font"]
    key = (family, size, weight)
    cached = _font_cache.get(key)
    if cached is None:
        cached = ctk.CTkFont(family=family, size=size, weight=weight)
        _font_cache[key] = cached
    return cached


def surface_style(theme, variant="surface"):
    variants = {
        "shell": {
            "fg_color": theme["shell_bg"],
            "border_color": theme["border_soft"],
            "corner_radius": theme["radius_lg"],
        },
        "panel": {
            "fg_color": theme["panel"],
            "border_color": theme["border"],
            "corner_radius": theme["radius_lg"],
        },
        "surface": {
            "fg_color": theme["surface"],
            "border_color": theme["border"],
            "corner_radius": theme["radius_md"],
        },
        "surface_alt": {
            "fg_color": theme["surface_alt"],
            "border_color": theme["border_soft"],
            "corner_radius": theme["radius_md"],
        },
        "soft": {
            "fg_color": theme["surface_soft"],
            "border_color": theme["border_soft"],
            "corner_radius": theme["radius_md"],
        },
        "emphasis": {
            "fg_color": theme["surface_emphasis"],
            "border_color": theme["border_strong"],
            "corner_radius": theme["radius_md"],
        },
    }
    return variants.get(variant, variants["surface"]).copy()


def button_style(theme, variant="primary"):
    variants = {
        "primary": {
            "fg_color": theme["accent"],
            "hover_color": theme["accent_hover"],
            "text_color": theme["text_on_accent"],
            "border_width": 1,
            "border_color": theme["accent"],
        },
        "secondary": {
            "fg_color": theme["surface"],
            "hover_color": theme["surface_alt"],
            "text_color": theme["text"],
            "border_width": 1,
            "border_color": theme["border"],
        },
        "success": {
            "fg_color": theme["success"],
            "hover_color": theme["success_hover"],
            "text_color": theme["text_on_accent"],
            "border_width": 1,
            "border_color": theme["success"],
        },
        "warning": {
            "fg_color": theme["warning"],
            "hover_color": theme["warning_hover"],
            "text_color": theme["text_on_accent"],
            "border_width": 1,
            "border_color": theme["warning"],
        },
        "danger": {
            "fg_color": theme["danger"],
            "hover_color": theme["danger_hover"],
            "text_color": theme["text_on_accent"],
            "border_width": 1,
            "border_color": theme["danger"],
        },
        "ghost": {
            "fg_color": "transparent",
            "hover_color": theme["surface"],
            "text_color": theme["text_soft"],
            "border_width": 1,
            "border_color": theme["border_soft"],
        },
        "nav": {
            "fg_color": theme["nav_idle"],
            "hover_color": theme["nav_hover"],
            "text_color": theme["text_soft"],
            "border_width": 1,
            "border_color": theme["border_soft"],
        },
        "nav_active": {
            "fg_color": theme["nav_active_bg"],
            "hover_color": theme["nav_active_bg"],
            "text_color": theme["text"],
            "border_width": 1,
            "border_color": theme["nav_active_border"],
        },
    }
    return variants.get(variant, variants["primary"]).copy()


def entry_style(theme):
    return {
        "fg_color": theme["input_bg"],
        "border_color": theme["border"],
        "text_color": theme["text"],
        "placeholder_text_color": theme["muted_soft"],
        "corner_radius": theme["radius_sm"],
    }


def combo_style(theme):
    return {
        "fg_color": theme["input_bg"],
        "border_color": theme["border"],
        "button_color": theme["surface"],
        "button_hover_color": theme["surface_alt"],
        "text_color": theme["text"],
        "dropdown_fg_color": theme["panel"],
        "dropdown_hover_color": theme["surface"],
        "dropdown_text_color": theme["text"],
        "corner_radius": theme["radius_sm"],
    }


def checkbox_style(theme):
    return {
        "fg_color": theme["accent"],
        "hover_color": theme["accent_hover"],
        "border_color": theme["border"],
        "checkmark_color": theme["text_on_accent"],
        "text_color": theme["text_soft"],
    }
