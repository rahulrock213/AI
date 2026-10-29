#!/usr/bin/env python3
"""Usage: python make_video.py quizzes/<file>.json  ->  build/<name>.mp4"""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from quizvideo.tts import duration, speak


def ass_time(t):
    return f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}"


def write_captions(spec, starts, path, size):
    """Burned-in captions: one line of text per narrated sentence (ASS subtitle file)."""
    w, h = size
    head = (
        f"[Script Info]\nScriptType: v4.00+\nPlayResX: {w}\nPlayResY: {h}\nWrapStyle: 0\n\n"
        "[V4+ Styles]\nFormat: Name,Fontname,Fontsize,PrimaryColour,OutlineColour,BackColour,Bold,"
        "Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,"
        "Alignment,MarginL,MarginR,MarginV,Encoding\n"
        f"Style: Default,DejaVu Sans,{round(w / 20)},&H00FFFFFF,&H00000000,&H80000000,1,0,0,0,"
        f"100,100,0,0,1,4,1,2,{round(w / 15)},{round(w / 15)},{round(h * 0.04)},1\n\n"
        "[Events]\nFormat: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text\n")
    lines = []
    for sc, start in zip(spec["scenes"], starts):
        for a, b, text in sc["sentences"]:
            lines.append(f"Dialogue: 0,{ass_time(start + a)},{ass_time(start + b + 0.3)},"
                         f"Default,,0,0,0,,{text}")
    path.write_text(head + "\n".join(lines) + "\n")


def make_sfx(work):
    """Tiny synthesized sound effects (no downloads): pop, tick, ding, tada."""
    def tone(freq, secs, delay=0.0, vol=0.5):
        return (f"sine=f={freq}:d={secs}", f"afade=t=out:st={secs * 0.3:.2f}:d={secs * 0.7:.2f},"
                f"volume={vol},adelay={round(delay * 1000)}:all=1")
    sounds = {"pop": [tone(520, 0.14), tone(780, 0.1, 0.03, 0.3)],
              "tick": [tone(1000, 0.05, 0, 0.35)],
              "ding": [tone(988, 0.5, 0, 0.5), tone(1319, 0.7, 0.12, 0.4)],
              "tada": [tone(523, 0.2, 0), tone(659, 0.2, 0.14), tone(784, 0.2, 0.28), tone(1047, 0.8, 0.42)]}
    paths = {}
    for name, notes in sounds.items():
        path = work / f"sfx_{name}.wav"
        cmd = ["ffmpeg", "-y", "-loglevel", "error"]
        for src, _ in notes:
            cmd += ["-f", "lavfi", "-i", src]
        chains = [f"[{i}:a]{f}[n{i}]" for i, (_, f) in enumerate(notes)]
        mixed = "".join(f"[n{i}]" for i in range(len(notes))) + f"amix=inputs={len(notes)}:normalize=0[o]"
        subprocess.run(cmd + ["-filter_complex", ";".join(chains + [mixed]), "-map", "[o]", str(path)], check=True)
        paths[name] = path.resolve()
    return paths


def mix(spec, video, times, work, out):
    """Narration (+ optional quiet music) and captions onto the Manim video."""
    total = duration(video)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", str(video)]
    for sc in spec["scenes"]:
        cmd += ["-i", sc["audio"]]
    n = len(spec["scenes"])
    parts = []
    for i, start in enumerate(times["starts"]):
        parts.append(f"[{i + 1}:a]adelay={round(start * 1000)}:all=1[a{i}]")
    labels = [f"[a{i}]" for i in range(n)]
    events = times.get("events", [])
    if events:  # sound effects ride along with the voice
        paths = make_sfx(work)
        for j, (t, name) in enumerate(events):
            cmd += ["-i", str(paths[name])]
            parts.append(f"[{n + 1 + j}:a]adelay={round(t * 1000)}:all=1,volume={spec.get('sfx_volume', 0.5)}[s{j}]")
            labels.append(f"[s{j}]")
    parts.append("".join(labels) + f"amix=inputs={len(labels)}:normalize=0:duration=longest[voice]")
    music = spec.get("music")
    if music and Path(music).exists():
        cmd += ["-stream_loop", "-1", "-i", str(Path(music).resolve())]
        vol = spec.get("music_volume", 0.12)
        parts.append(f"[{n + 1 + len(events)}:a]volume={vol},atrim=0:{total:.2f},afade=t=out:st={total - 2:.2f}:d=2[bg]")
        parts.append("[voice][bg]amix=inputs=2:normalize=0:duration=first[aud]")
    else:
        if music:
            print(f"[music] file not found: {music} (skipping)")
        parts.append("[voice]anull[aud]")
    if spec.get("captions", True):
        size = (1080, 1920) if spec.get("aspect", "vertical") == "vertical" else None
        if size is None:
            w, h = probe_size(video)
        else:
            w, h = size
        write_captions(spec, times["starts"], work / "captions.ass", (w, h))
        parts.append("[0:v]ass=captions.ass[vid]")
        vmap = ["-map", "[vid]"]
    else:
        vmap = ["-map", "0:v", "-c:v", "copy"]
    cmd += ["-filter_complex", ";".join(parts), *vmap, "-map", "[aud]", "-t", f"{total:.2f}",
            "-c:a", "aac", str(out)]
    subprocess.run(cmd, check=True, cwd=work)


def probe_size(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
         "-of", "csv=p=0", str(path)], capture_output=True, text=True, check=True)
    w, h = out.stdout.strip().split(",")
    return int(w), int(h)


def main(path):
    spec = json.load(open(path))
    name = Path(path).stem
    work = Path("build") / name
    work.mkdir(parents=True, exist_ok=True)
    kids = spec.get("style") == "kids"
    voice = spec.get("voice", "en-US-AnaNeural" if kids else "en-US-AndrewNeural")
    rate = spec.get("rate", "-8%" if kids else "+0%")  # kids: a touch slower
    pitch = spec.get("pitch", "+0Hz")
    for i, sc in enumerate(spec["scenes"]):
        audio = work / f"scene{i}.mp3"
        sc["audio"] = str(audio.resolve())
        secs, sc["sentences"] = speak(sc["narration"], voice, audio, rate, pitch)
        sc["duration"] = secs + 0.4
    resolved = work / "spec.json"
    resolved.write_text(json.dumps(spec))
    times_file = work / "times.json"
    env = dict(os.environ, QUIZ_SPEC=str(resolved.resolve()), QUIZ_TIMES=str(times_file.resolve()))
    quality = spec.get("quality", "m")
    subprocess.run(
        [sys.executable, "-m", "manim", f"-q{quality}", "--media_dir", str(work / "media"),
         "-o", name, "quizvideo/scene.py", "QuizScene"], check=True, env=env)
    found = next((work / "media" / "videos").rglob(f"{name}.mp4"))
    out = Path("build") / f"{name}.mp4"
    mix(spec, found.resolve(), json.load(open(times_file)), work, out.resolve())
    print(f"\nDone: {out}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
