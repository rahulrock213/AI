"""Narration: free Microsoft Edge voices via edge-tts, silent fallback if offline."""
import asyncio
import re
import subprocess
from pathlib import Path

try:
    import edge_tts
except ImportError:
    edge_tts = None


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


def _sentences(text, secs):
    """Split text into sentences, timed in proportion to their length (used without voice timings)."""
    parts = [p for p in re.split(r"(?<=[.!?])\s+", text.strip()) if p]
    total = sum(len(p) for p in parts) or 1
    out, t = [], 0.0
    for p in parts:
        end = t + secs * len(p) / total
        out.append((t, end, p))
        t = end
    return out


async def _save(text, voice, path):
    """Save the voice audio and return the (start, end, sentence) timings edge-tts reports."""
    comm = edge_tts.Communicate(text, voice, boundary="SentenceBoundary")
    sentences = []
    with open(path, "wb") as f:
        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "SentenceBoundary":
                start = chunk["offset"] / 1e7  # 100-nanosecond units
                sentences.append((start, start + chunk["duration"] / 1e7, chunk["text"]))
    return sentences


def speak(text, voice, path):
    """Write narration audio to path. Returns (audio seconds, [(start, end, sentence), ...])."""
    path = Path(path)
    try:
        sentences = asyncio.run(_save(text, voice, path))
        if path.stat().st_size == 0:
            raise RuntimeError("empty audio")
    except Exception as e:  # offline / blocked network
        print(f"[tts] voice unavailable ({type(e).__name__}); using silent audio")
        _silent(text, path)
        sentences = []
    secs = duration(path)
    return secs, sentences or _sentences(text, secs)
