from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any


@dataclass
class Playlist:
    id: str
    title: str
    url: str
    status: str = "new"


@dataclass
class Track:
    id: str  # owner_id_audio_id
    playlist_id: str
    artist: str
    title: str

    # Metadata
    owner_id: str
    audio_id: str
    duration: int = 0
    subtitle: str = ""
    cover_url: str = ""
    access_key: str = ""

    # Technical
    url: str = ""  # masked or direct
    action_hash: str = ""
    url_hash: str = ""

    # Extended Metadata
    album_obj: Optional[Dict] = None
    main_artists: List[Dict] = field(default_factory=list)
    feat_artists: List[Dict] = field(default_factory=list)
    genre_id: int = 0
    date: int = 0

    # Download state
    status: str = "pending"
    local_path: Optional[str] = None

    # Telegram state
    tg_status: str = "pending"
    tg_message_id: Optional[str] = None
    tg_file_id: Optional[str] = None
    source: str = "vk"

