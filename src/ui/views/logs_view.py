import customtkinter as ctk
import datetime

class LogsView(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        
        self.textbox = ctk.CTkTextbox(self)
        self.textbox.pack(fill="both", expand=True, padx=20, pady=20)
        self.textbox.configure(state="disabled")

    def append(self, text):
        self.textbox.configure(state="normal")
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        self.textbox.insert("end", f"[{ts}] {text}\n")
        self.textbox.see("end")
        self.textbox.configure(state="disabled")
