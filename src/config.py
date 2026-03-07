import os
import sys

# Определяем корень проекта
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


if getattr(sys, "frozen", False):
    APP_DIR = os.path.dirname(sys.executable)
    if hasattr(sys, "_MEIPASS"):
        RESOURCE_DIR = sys._MEIPASS
    else:
        # PyInstaller 6+ default onedir bundle is in _internal
        internal_dir = os.path.join(APP_DIR, "_internal")
        if os.path.exists(internal_dir):
            RESOURCE_DIR = internal_dir
        else:
            RESOURCE_DIR = APP_DIR
else:
    APP_DIR = BASE_DIR
    RESOURCE_DIR = BASE_DIR

# Папка для бинарников (автоскачивание при первом запуске)
BIN_DIR = os.path.join(APP_DIR, "bin")

# Папки данных
DATA_DIR = os.path.join(APP_DIR, "data")
PROFILE_DIR = os.path.join(DATA_DIR, "chrome_profile")
DOWNLOAD_DIR = os.path.join(DATA_DIR, "downloads")

# Файлы данных
DB_PATH = os.path.join(DATA_DIR, "vk_music.db")
LOG_PATH = os.path.join(DATA_DIR, "app.log")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(PROFILE_DIR, exist_ok=True)
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(BIN_DIR, exist_ok=True)

# FFmpeg path: resolved lazily via BinaryManager.ensure_ffmpeg()
# in ffmpeg_service.py.  This constant is a *default guess* for
# backward compatibility with frozen (PyInstaller) builds that
# ship the binary inside the bundle.
FFMPEG_PATH: str = ""
for _candidate in [
    os.path.join(BIN_DIR, "ffmpeg.exe" if sys.platform == "win32" else "ffmpeg"),
    os.path.join(RESOURCE_DIR, "bin", "ffmpeg.exe" if sys.platform == "win32" else "ffmpeg"),
]:
    if os.path.isfile(_candidate):
        FFMPEG_PATH = _candidate
        break

# Security notice: the Chrome profile at PROFILE_DIR stores session cookies
# for VK and Yandex.  Any local process on this machine has read access to them.
# Consider using OS-level file permissions to restrict the data/ directory if needed.
if sys.platform == "win32":
    try:
        import stat
        _data_stat = os.stat(DATA_DIR)
    except Exception:
        pass

# VK Genres Mapping
VK_GENRES = {
    1: "Rock",
    2: "Pop",
    3: "Rap & Hip-Hop",
    4: "Easy Listening",
    5: "Dance & House",
    6: "Instrumental",
    7: "Metal",
    8: "Dubstep",
    1001: "Jazz & Blues",
    10: "Drum & Bass",
    11: "Trance",
    12: "Chanson",
    13: "Ethnic",
    14: "Acoustic & Vocal",
    15: "Reggae",
    16: "Classical",
    17: "Indie Pop",
    18: "Другое",
    19: "Speech",
    21: "Alternative",
    22: "Electropop & Disco",
}

# JS Scripts
JS_FIND_USER_ID = "return window.vk ? window.vk.id : null;"

JS_SCROLL_HEIGHT = "return document.body.scrollHeight"

JS_SCROLL_TO_BOTTOM = "window.scrollTo(0, document.body.scrollHeight);"

JS_PARSE_TRACKS = """
const getReactFiber = (el) => {
    const key = Object.keys(el).find(k => k.startsWith('__reactFiber') || k.startsWith('__reactProps'));
    return key ? el[key] : null;
};

const findApiAudioAndMeta = (fiber) => {
    let curr = fiber;
    let depth = 0;
    let res = { audio: null, hashes: "" };
    while (curr && depth < 40) {
        const p = curr.memoizedProps || curr.props || {};
        const a = p.audio?.apiAudio || p.audio || p.track?.data?.apiAudio || p.track?.entity?.apiAudio;
        if (a && a.id && !res.audio) res.audio = a;
        const h = p.hashes || (p.audio && p.audio.hashes) || (p.track && p.track.hashes);
        if (h && typeof h === 'string' && h.includes('/') && !res.hashes) res.hashes = h;
        if (res.audio && res.hashes) break;
        curr = curr.return;
        depth++;
    }
    return res;
};

const rows = document.querySelectorAll('.audio_row, [class*="AudioRow__root"]');
const results = [];
rows.forEach((row, index) => {
    const fiber = getReactFiber(row);
    const { audio: a, hashes: hStr } = findApiAudioAndMeta(fiber);
    if (a) {
        row.setAttribute('data-vms-temp-id', index);
        const h = (hStr || a.hashes || "").split('/');
        
        results.push({
            temp_id: index,
            id: a.owner_id + '_' + a.id,
            owner_id: a.owner_id,
            audio_id: a.id,
            artist: a.artist || a.performer || "Unknown",
            title: a.title || "Unknown",
            subtitle: a.subtitle || a.subTitle || "",
            duration: a.duration || 0,
            url: a.url || "",
            action_hash: a.actionHash || a.action_hash || h[2] || "",
            url_hash: a.urlHash || a.url_hash || h[5] || "",
            access_key: a.accessKey || a.access_key || h[0] || "",
            
            album_obj: a.album || null,
            main_artists: a.main_artists || a.mainArtists || [],
            feat_artists: a.featured_artists || a.featArtists || [],
            genre_id: a.genre_id || 0,
            date: a.date || 0,
            cover_url: (a.album && a.album.thumb) ? (a.album.thumb.photo_1200 || a.album.thumb.photo_600 || a.album.thumb.photo_300) : ""
        });
    }
});
return results;
"""

JS_UNKASK_URL = """
const a = arguments[0];
return new Promise((resolve) => {
    const vkId = window.vk ? window.vk.id : 0;
    const clean = (url) => {
        if (url && window.AudioUtils && window.AudioUtils.unmaskSource) {
            return window.AudioUtils.unmaskSource(url, vkId);
        }
        return url;
    };

    if (a.url && a.url.length > 10) {
        const decoded = clean(a.url);
        if (decoded && decoded.startsWith('http')) {
            return resolve(['DIRECT_DECODE', decoded]);
        }
    }

    const fullId = [a.owner_id, a.audio_id, a.access_key].filter(Boolean).join('_');
    window.ajax.post('al_audio.php', { act: 'get_audio_by_id', ids: fullId }, {
        onDone: (res) => {
            if (res && res[0] && res[0][2]) {
                const url = clean(res[0][2]);
                if (url && url.startsWith('http')) return resolve(['PLAN_A', url]);
            }

            const reloadIds = [a.owner_id, a.audio_id, a.action_hash, a.url_hash].join('_');
            window.ajax.post('al_audio.php', { act: 'reload_audio', ids: reloadIds, al: 1 }, {
                onDone: (reRes) => {
                    try {
                        const tuple = reRes[0][0];
                        const url = clean(tuple[2]);
                        if (url && url.startsWith('http')) resolve(['PLAN_B', url]);
                        else resolve(['FAIL', 'no_url_in_res']);
                    } catch(e) { resolve(['FAIL', 'parse_error']); }
                },
                onFail: (err) => resolve(['FAIL', 'ajax_fail_b'])
            });
        },
        onFail: (err) => resolve(['FAIL', 'ajax_fail_a'])
    });
});
"""

JS_EXPAND_BUTTON = "arguments[0].scrollIntoView({block: 'center'});"
JS_CLICK = "arguments[0].click();"
