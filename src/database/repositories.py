from src.database.db_manager import DBManager
from src.domain.models import Playlist, Track
import json


class PlaylistRepository:
    def __init__(self):
        self.conn = DBManager().get_connection()

    def save(self, playlist: Playlist):
        cursor = self.conn.cursor()
        try:
            cursor.execute(
                "INSERT OR IGNORE INTO playlists (id, title, url, status) VALUES (?, ?, ?, ?)",
                (playlist.id, playlist.title, playlist.url, playlist.status),
            )
            self.conn.commit()
        except Exception as e:
            print(f"DB Error (PlaylistRepository.save): {e}")

    def get_all(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, title, url, status FROM playlists")
        return [Playlist(*row) for row in cursor.fetchall()]

    def get_count(self):
        cursor = self.conn.cursor()
        try:
            cursor.execute("SELECT COUNT(*) FROM playlists")
            res = cursor.fetchone()
            return res[0] if res else 0
        except Exception as e:
            print(f"DB Error (PlaylistRepository.get_count): {e}")
            return 0


class TrackRepository:
    def __init__(self):
        self.conn = DBManager().get_connection()

    def save(self, track: Track):
        cursor = self.conn.cursor()
        try:
            # We persist minimal info for the list, plus maybe some JSON for complex fields if needed later?
            # Ideally we might want to store more columns if we want to resume fully.
            # For MVP refactor, we stick to the existing schema but passed ID is crucial.
            # Note: The existing schema (from old_main) had restricted columns.
            # We will use what we have in the DB schema defined in DBManager.

            cursor.execute(
                """
                INSERT OR IGNORE INTO tracks 
                (id, playlist_id, artist, title, cover_url, status, local_path) 
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    track.id,
                    track.playlist_id,
                    track.artist,
                    track.title,
                    track.cover_url,
                    track.status,
                    track.local_path,
                ),
            )
            self.conn.commit()
        except Exception as e:
            print(f"DB Error (TrackRepository.save): {e}")

    def update_status(self, track_id: str, status: str, local_path: str = None):
        cursor = self.conn.cursor()
        if local_path:
            cursor.execute(
                "UPDATE tracks SET status = ?, local_path = ? WHERE id = ?",
                (status, local_path, track_id),
            )
        else:
            cursor.execute(
                "UPDATE tracks SET status = ? WHERE id = ?", (status, track_id)
            )
        self.conn.commit()

    def update_tg_status(
        self, track_id: str, status: str, message_id: str = None, file_id: str = None
    ):
        cursor = self.conn.cursor()
        query = "UPDATE tracks SET tg_status = ?"
        params = [status]
        if message_id:
            query += ", tg_message_id = ?"
            params.append(message_id)
        if file_id:
            query += ", tg_file_id = ?"
            params.append(file_id)

        query += " WHERE id = ?"
        params.append(track_id)

        try:
            cursor.execute(query, tuple(params))
            self.conn.commit()
        except Exception as e:
            print(f"DB Error (TrackRepository.update_tg_status): {e}")

    def get_stats(self):
        cursor = self.conn.cursor()
        stats = {"total": 0, "downloaded": 0, "uploaded": 0}
        try:
            cursor.execute("SELECT COUNT(*) FROM tracks")
            res = cursor.fetchone()
            stats["total"] = res[0] if res else 0

            cursor.execute("SELECT COUNT(*) FROM tracks WHERE status = 'downloaded'")
            res = cursor.fetchone()
            stats["downloaded"] = res[0] if res else 0

            cursor.execute("SELECT COUNT(*) FROM tracks WHERE tg_status = 'uploaded'")
            res = cursor.fetchone()
            stats["uploaded"] = res[0] if res else 0
        except Exception as e:
            print(f"DB Error (TrackRepository.get_stats): {e}")
        return stats
