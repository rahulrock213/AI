"""Narration: free Microsoft Edge voices via edge-tts, silent fallback if offline."""
import asyncio
import subprocess
from pathlib import Path


def duration(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", str(path)],
        capture_output=True, text=True, check=True)
    return float(out.stdout.strip())


def _silent(text, path):
    secs = max(2.0, len(text.split()) / 2.5)  # ~150 words per minute
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i",
         "anullsrc=r=24000:cl=mono", "-t", f"{secs:.2f}", "-q:a", "9", str(path)],
        check=True)


def speak(text, voice, path):
    path = Path(path)
    try:
        import edge_tts
        asyncio.run(edge_tts.Communicate(text, voice).save(str(path)))
        if path.stat().st_size == 0:
            raise RuntimeError("empty audio")
    except Exception as e:  # offline / blocked network
        print(f"[tts] voice unavailable ({type(e).__name__}); using silent audio")
        _silent(text, path)
    return duration(path)
