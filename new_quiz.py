#!/usr/bin/env python3
"""Usage: python new_quiz.py  ->  asks for a question and answer, writes quizzes/<name>.json"""
import json
import re
from pathlib import Path


def ask(prompt, default=""):
    text = input(f"{prompt}{f' [{default}]' if default else ''}: ").strip()
    return text or default


def main():
    print("Make a starter quiz video. Press Enter to accept the [default].\n")
    question = ask("Question (e.g. A bat and ball cost $1.10 ...)")
    answer = ask("Answer (e.g. The ball costs 5 cents)")
    if not question or not answer:
        raise SystemExit("A question and an answer are both needed.")
    wrong = ask("Common wrong answer (optional)")
    title = ask("Short title", " ".join(question.split()[:4]))
    name = ask("File name", re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_") or "my_quiz")
    aspect = ask("Shape: vertical (Shorts/Reels) or wide (YouTube)", "vertical")
    if aspect not in ("vertical", "wide"):
        raise SystemExit("Shape must be vertical or wide.")

    scenes = [{
        "narration": f"Can you solve this? {question}",
        "steps": [{"do": "title", "text": title, "color": "yellow"},
                  {"do": "text", "text": question}]}]
    scenes.append({
        "narration": "Pause the video and think about it!",
        "steps": [{"do": "timer", "secs": 5, "text": "Think about it!"}]})
    if wrong:
        scenes.append({
            "narration": f"Many people say {wrong}. But that is not right!",
            "steps": [{"do": "text", "text": f"Common guess: {wrong}", "color": "red"},
                      {"do": "text", "text": "Not quite!", "color": "red"}]})
    scenes.append({
        "narration": f"The answer is: {answer}. Follow for more tricky puzzles!",
        "steps": [{"do": "title", "text": answer, "color": "green"},
                  {"do": "text", "text": "Follow for more puzzles!", "color": "yellow"}]})

    spec = {"title": title, "voice": "en-US-AndrewNeural", "aspect": aspect,
            "quality": "m", "scenes": scenes}
    path = Path("quizzes") / f"{name}.json"
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n")
    print(f"\nCreated {path}. Edit it to add steps (see README), then run:")
    print(f"    python make_video.py {path}")


if __name__ == "__main__":
    main()
