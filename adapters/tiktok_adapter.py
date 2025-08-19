from yt_dlp import YoutubeDL

def fetch_tiktok(url: str) -> dict:
    ydl_opts = {"quiet": True, "dump_single_json": True, "skip_download": True}
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
    return {
        "platform": "tiktok",
        "id": info.get("id"),
        "uploader": info.get("uploader"),
        "description": info.get("description") or "",
        "webpage_url": info.get("webpage_url") or url,
        "duration": info.get("duration"),
        "timestamp": info.get("timestamp"),
        "view_count": info.get("view_count"),
        "like_count": info.get("like_count"),
    }
