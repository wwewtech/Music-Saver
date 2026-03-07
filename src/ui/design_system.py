import customtkinter as ctk


def get_theme():
    return {
        "font": "Segoe UI",
        "font_alt": "Segoe UI",
        "font_fallback": "Segoe UI",
        "bg": "#09090b",
        "panel": "#111113",
        "card": "#141417",
        "surface": "#18181b",
        "surface_alt": "#232329",
        "text": "#fafafa",
        "text_on_accent": "#09090b",
        "muted": "#a1a1aa",
        "accent": "#fafafa",
        "accent_hover": "#e4e4e7",
        "success": "#10b981",
        "success_hover": "#059669",
        "warning": "#f59e0b",
        "warning_hover": "#d97706",
        "danger": "#d24b57",
        "border": "#2a2a32",
        "nav_idle": "#141417",
        "nav_hover": "#232329",
        "input_bg": "#111113",
    }


def ui_font(theme, size, weight="normal", alt=False):
    family = theme["font_alt"] if alt else theme["font"]
    return ctk.CTkFont(family=family, size=size, weight=weight)


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
            "hover_color": theme["nav_hover"],
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
        "ghost": {
            "fg_color": "transparent",
            "hover_color": theme["surface_alt"],
            "text_color": theme["muted"],
            "border_width": 1,
            "border_color": theme["border"],
        },
        "nav": {
            "fg_color": theme["nav_idle"],
            "hover_color": theme["nav_hover"],
            "text_color": theme["text"],
            "border_width": 1,
            "border_color": theme["border"],
        },
        "nav_active": {
            "fg_color": theme["accent"],
            "hover_color": theme["accent_hover"],
            "text_color": theme["text_on_accent"],
            "border_width": 1,
            "border_color": theme["accent"],
        },
    }
    return variants.get(variant, variants["primary"]).copy()


def entry_style(theme):
    return {
        "fg_color": theme["input_bg"],
        "border_color": theme["border"],
        "text_color": theme["text"],
        "corner_radius": 10,
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
        "corner_radius": 10,
    }


def checkbox_style(theme):
    return {
        "fg_color": theme["accent"],
        "hover_color": theme["accent_hover"],
        "border_color": theme["border"],
        "checkmark_color": theme["text_on_accent"],
        "text_color": theme["text"],
    }
