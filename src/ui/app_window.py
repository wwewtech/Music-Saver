import customtkinter as ctk
from src.ui.views.dashboard_view import DashboardView
from src.ui.views.downloader_view import DownloaderView
from src.ui.views.telegram_view import TelegramView
from src.ui.views.logs_view import LogsView

class AppWindow(ctk.CTk):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        
        self.title("VK Music Saver Pro - Admin Panel")
        self.geometry("1100x700")
        
        # Configure Controller Callbacks
        self.controller.on_log = self.log_message
        self.controller.on_scan_complete = self.on_scan_complete
        self.controller.on_progress = self.on_progress
        self.controller.on_download_complete = self.on_download_complete
        self.controller.on_login_success = self.on_login_success
        
        # Hook for strategy
        self.controller.get_current_strategy = self.get_strategy_from_ui
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        
        self.setup_sidebar()
        self.setup_views()
        
        # Start Clock/Stats Loop
        self.update_stats_loop()

    def setup_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        self.lbl_logo = ctk.CTkLabel(self.sidebar, text="VK SAVER PRO", font=("Roboto", 20, "bold"))
        self.lbl_logo.pack(pady=30)
        
        self.btn_dash = self.create_nav_btn("📊 Dashboard", "dashboard")
        self.btn_vk = self.create_nav_btn("🎧 VK Downloader", "vk")
        self.btn_tg = self.create_nav_btn("✈️ Telegram", "tg")
        self.btn_logs = self.create_nav_btn("📝 Logs", "logs")
        
        # Small footer
        lbl_ver = ctk.CTkLabel(self.sidebar, text="v2.0 Checkpoint", text_color="gray", font=("Arial", 10))
        lbl_ver.pack(side="bottom", pady=10)

    def create_nav_btn(self, text, view_name):
        btn = ctk.CTkButton(self.sidebar, text=text, fg_color="transparent", anchor="w", 
                            height=40, font=("Roboto", 14),
                            command=lambda: self.show_view(view_name))
        btn.pack(fill="x", padx=10, pady=5)
        return btn

    def setup_views(self):
        self.view_container = ctk.CTkFrame(self, fg_color="transparent")
        self.view_container.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.view_container.grid_rowconfigure(0, weight=1)
        self.view_container.grid_columnconfigure(0, weight=1)
        
        self.views = {}
        self.views["dashboard"] = DashboardView(self.view_container, self.controller)
        self.views["vk"] = DownloaderView(self.view_container, self.controller)
        self.views["tg"] = TelegramView(self.view_container, self.controller)
        self.views["logs"] = LogsView(self.view_container)
        
        # Init default
        self.show_view("dashboard")

    def show_view(self, name):
        # Hide all
        for v in self.views.values():
            v.grid_forget()
        
        # Reset butons
        for btn in [self.btn_dash, self.btn_vk, self.btn_tg, self.btn_logs]:
            btn.configure(fg_color="transparent")
            
        # Highlight active
        btn_map = {
            "dashboard": self.btn_dash,
            "vk": self.btn_vk,
            "tg": self.btn_tg,
            "logs": self.btn_logs
        }
        if name in btn_map:
            btn_map[name].configure(fg_color=["#3B8ED0", "#1F6AA5"])

        # Show one
        self.views[name].grid(row=0, column=0, sticky="nsew")

    def log_message(self, msg):
        self.after(0, lambda: self.views["logs"].append(msg))
    
    def on_scan_complete(self, playlists):
        self.after(0, lambda: self.views["vk"].update_playlists(playlists))
        self.on_log_message("Playlists received. Switching view...")
        self.after(100, lambda: self.show_view("vk"))

    def on_progress(self, val):
        pass # Optional: Add progress bar to sidebar if requested.

    def on_download_complete(self):
        self.log_message("✅ ALl TASKS COMPLETED.")
        
    def on_login_success(self):
        self.log_message("Login Successful. You can now scan playlists.")
        self.views["vk"].lbl_status.configure(text="Status: Connected", text_color="green")
    
    def on_log_message(self, msg):
        # Compatibility wrapper
        self.log_message(msg)

    def get_strategy_from_ui(self):
        return self.views["tg"].get_strategy()

    def update_stats_loop(self):
        # Update dashboard every 5s
        if self.views.get("dashboard"):
            try:
                self.views["dashboard"].update_stats()
            except:
                pass
        self.after(5000, self.update_stats_loop)

    def on_close(self):
        try:
            self.controller.close_app()
        except:
            pass
        self.destroy()
