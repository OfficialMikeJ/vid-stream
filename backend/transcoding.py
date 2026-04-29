"""Transcoding preset definitions and helpers.

A preset describes how `process_video()` should produce the HLS output:
- video_codec, video_bitrate, audio_bitrate
- scale: max output height (-1 keeps source if smaller)
- copy_video / copy_audio: skip re-encode for fastest processing
"""

PRESETS = {
    "source": {
        "label": "Source (no re-encode)",
        "description": "Fastest — copies the source video and audio streams as-is. Use when the source is already a web-friendly H.264/AAC MP4.",
        "copy_video": True,
        "copy_audio": True,
        "scale": None,
        "video_bitrate": None,
        "audio_bitrate": None,
    },
    "1080p": {
        "label": "1080p High",
        "description": "Re-encodes to H.264 1080p (max height). Best quality, balanced file size.",
        "copy_video": False,
        "copy_audio": False,
        "scale": 1080,
        "video_bitrate": "5000k",
        "audio_bitrate": "192k",
    },
    "720p": {
        "label": "720p Standard",
        "description": "Re-encodes to H.264 720p. Recommended default — fast playback, smaller files.",
        "copy_video": False,
        "copy_audio": False,
        "scale": 720,
        "video_bitrate": "2800k",
        "audio_bitrate": "128k",
    },
    "480p": {
        "label": "480p Low-bandwidth",
        "description": "Re-encodes to 480p for slow connections. Smallest files.",
        "copy_video": False,
        "copy_audio": False,
        "scale": 480,
        "video_bitrate": "1200k",
        "audio_bitrate": "96k",
    },
}

DEFAULT_PRESET_KEY = "source"


def get_preset(key: str) -> dict:
    """Return the preset config for `key`, falling back to source."""
    return PRESETS.get(key, PRESETS[DEFAULT_PRESET_KEY])


def list_presets() -> list:
    """Return all presets as a list of {key, label, description}."""
    return [
        {"key": k, "label": v["label"], "description": v["description"]}
        for k, v in PRESETS.items()
    ]
