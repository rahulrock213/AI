#!/usr/bin/env python3
"""Usage: python make_video.py quizzes/<file>.json  ->  build/<name>.mp4"""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from quizvideo.tts import speak


def main(path):
    spec = json.load(open(path))
    name = Path(path).stem
    work = Path("build") / name
    work.mkdir(parents=True, exist_ok=True)
    voice = spec.get("voice", "en-US-AndrewNeural")
    for i, sc in enumerate(spec["scenes"]):
        audio = work / f"scene{i}.mp3"
        sc["audio"] = str(audio.resolve())
        sc["duration"] = speak(sc["narration"], voice, audio) + 0.4
    resolved = work / "spec.json"
    resolved.write_text(json.dumps(spec))
    env = dict(os.environ, QUIZ_SPEC=str(resolved.resolve()))
    quality = spec.get("quality", "m")
    subprocess.run(
        [sys.executable, "-m", "manim", f"-q{quality}", "--media_dir", str(work / "media"),
         "-o", name, "quizvideo/scene.py", "QuizScene"], check=True, env=env)
    found = next((work / "media" / "videos").rglob(f"{name}.mp4"))
    out = Path("build") / f"{name}.mp4"
    shutil.copy(found, out)
    print(f"\nDone: {out}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
