import sqlite3
import os
from src.config import DB_PATH, DATA_DIR


class DBManager:
    _instance = None
    _connection = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DBManager, cls).__new__(cls)
            cls._instance._init_connection()
        return cls._instance

    def _init_connection(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        self._connection = sqlite3.connect(DB_PATH, check_same_thread=False)
        self._create_tables()

    def get_connection(self):
        return self._connection

    def _create_tables(self):
        cursor = self._connection.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS playlists (
                id TEXT PRIMARY KEY,
                title TEXT,
                url TEXT,
                status TEXT DEFAULT 'new'
            )
        """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS tracks (
                id TEXT PRIMARY KEY,
                playlist_id TEXT,
                artist TEXT,
                title TEXT,
                cover_url TEXT,
                local_path TEXT,
                status TEXT DEFAULT 'pending', 
                FOREIGN KEY(playlist_id) REFERENCES playlists(id)
            )
        """
        )
        self._upgrade_schema()
        self._connection.commit()

    def _upgrade_schema(self):
        cursor = self._connection.cursor()
        try:
            # Check if columns exist, if not add them
            cursor.execute("SELECT tg_status FROM tracks LIMIT 1")
        except sqlite3.OperationalError:
            cursor.execute(
                "ALTER TABLE tracks ADD COLUMN tg_status TEXT DEFAULT 'pending'"
            )
            cursor.execute("ALTER TABLE tracks ADD COLUMN tg_message_id TEXT")
            cursor.execute("ALTER TABLE tracks ADD COLUMN tg_file_id TEXT")
            print("DB Schema upgraded: Added Telegram columns to tracks table.")

    def close(self):
        if self._connection:
            self._connection.close()
