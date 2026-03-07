import customtkinter as ctk


class PlaylistView(ctk.CTkScrollableFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, label_text="Плейлисты", **kwargs)
        self.checkboxes = []

    def update_playlists(self, playlists_objects):
        # Clear
        for widget in self.winfo_children():
            widget.destroy()
        self.checkboxes = []

        for pl in playlists_objects:
            var = ctk.BooleanVar()
            chk = ctk.CTkCheckBox(self, text=pl.title, variable=var)
            chk.pack(anchor="w", padx=5, pady=2)
            self.checkboxes.append({"model": pl, "var": var})

    def get_selected(self):
        return [item["model"] for item in self.checkboxes if item["var"].get()]
