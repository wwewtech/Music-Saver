import customtkinter as ctk


class LogPanel(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.textbox = ctk.CTkTextbox(self, height=100, font=("Consolas", 11))
        self.textbox.pack(fill="both", expand=True, padx=5, pady=5)
        self.textbox.configure(state="disabled")

    def append_log(self, msg):
        self.textbox.configure(state="normal")
        self.textbox.insert("end", f"{msg}\n")
        self.textbox.see("end")
        self.textbox.configure(state="disabled")
