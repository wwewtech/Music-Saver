# 🎵 VK Music Saver

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![UI](https://img.shields.io/badge/UI-CustomTkinter-blueviolet.svg)

🚀 A powerful desktop application for downloading music from VK (Vkontakte) with automated tagging and a modern UI.
Built on top of Selenium and CustomTkinter, it provides a seamless experience for managing your offline music library.

---

## ✨ Features

- **📂 Automated Downloads**: high-speed track downloading using Selenium automation.
- **🏷️ Smart Tagging**:
  - Automatic ID3 metadata injection (Artist, Title, Album).
  - High-quality cover art embedding via `mutagen`.
- **🎨 Modern Interface**: clean, dark-themed UI based on `CustomTkinter`.
- **🎼 Library Management**:
  - Support for personal tracks, playlists, and albums.
  - Built-in SQLite database for tracking download history.
- **🛠️ Configurable**: easily adjustable download paths and Chrome profile management.

---

## 📋 Requirements

- **🐍 Python 3.10 or newer**
- **🌐 Google Chrome Browser** (latest version recommended)
- **📦 Key Dependencies**:
  - `customtkinter` (UI framework)
  - `selenium` (Web automation)
  - `mutagen` (Audio metadata processing)
  - `requests` (Network operations)

---

## 📥 Installation

### 🏗️ Setup from Source

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/vk-music-saver.git
   cd vk-music-saver
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # Windows
   .\venv\Scripts\activate
   # Linux/macOS
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

---

## 🚀 Usage

### 💻 Running the Application

```bash
python main.py
```

### ⚙️ Configuration
The application stores its data in the `data/` directory:
- `settings.json`: User preferences.
- `vk_music.db`: Local database of indexed tracks.
- `chrome_profile/`: Isolated browser profile for persistent sessions.

---

## 📁 Project Structure

- `src/ui/` — Interface components and views.
- `src/services/` — Core logic for VK interaction and file downloads.
- `src/domain/` — Data models and metadata processors.
- `src/database/` — Database management and repositories.
- `src/utils/` — Logging and auxiliary utilities.

---

## 👨‍💻 Development

To set up the development environment, ensure you have the required Python version and dependencies installed. The project uses a modular architecture for easy maintenance.

---

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## 🤝 Contributing

1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/amazing-feature`).
3. Commit your changes (`git commit -m 'Add some amazing feature'`).
4. Push to the branch (`git push origin feature/amazing-feature`).
5. Create a Pull Request.
