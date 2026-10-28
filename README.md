# AI Math Quiz Videos

Turn a tricky math question into a short animated, narrated video (Manim + free Edge voices).

## One-time setup (GitHub Codespaces)
1. On GitHub open this repo -> **Code -> Codespaces -> Create codespace on this branch**.
2. Wait a few minutes: it installs everything automatically.

## Make a video
In the Codespaces terminal:

    python make_video.py quizzes/bat_and_ball.json

The video appears in `build/bat_and_ball.mp4`. Right-click it in the file list -> Download.

## Make your own quiz
Copy `quizzes/bat_and_ball.json`, change the narration and steps (or ask Claude: "write a quiz JSON
like bat_and_ball.json for <your question>"). Step types: `title`, `text`, `math`, `box`, `pause`.
Colors: red, green, yellow, blue, orange, white. `aspect`: `vertical` (Shorts/Reels) or `wide`.
Change the voice with e.g. `en-IN-NeerjaNeural` or `en-GB-RyanNeural`.
