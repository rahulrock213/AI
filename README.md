# AI Math Quiz Videos

Turn a tricky math question into a short animated, narrated video (Manim + free Edge voices).
The narration, captions and animation are timed together, and the animation steps are spread
across the narration automatically.

## One-time setup (GitHub Codespaces)
1. On GitHub open this repo -> **Code -> Codespaces -> Create codespace on this branch**.
2. Wait a few minutes: it installs everything automatically.
   (Not in Codespaces? Run `bash .devcontainer/setup.sh`.)

## Make a video
In the terminal:

    python make_video.py quizzes/bat_and_ball.json

The video appears in `build/bat_and_ball.mp4`. Right-click it in the file list -> Download.
Examples: `sticker_puzzle_kids` (kids style), `bat_and_ball`, `monty_hall` (probability), `shortcut` (geometry), `magic_number` (number trick).

## Kids style (for 5-year-olds)
Add `"style": "kids"` to a quiz file (see `quizzes/sticker_puzzle_kids.json`). You get:
- a friendly mascot who blinks, bobs and moves its mouth while the voice talks, and hops on celebrations
- a child-like voice (`en-US-AnaNeural`, a little slower) - change with `voice`, `rate` (e.g. `"-15%"`), `pitch` (e.g. `"+10Hz"`)
- a colourful gradient background with floating bubbles, bouncy pop-in animations
- sound effects: pop on every new item, a tick for each second of the timer, ding, and a "tada"
  (turn one off per step with `"sfx": "none"`; loudness with `"sfx_volume"`, default `0.5`)
- `"celebrate": true` on any step fires confetti + tada + a mascot hop
- a `things` picture type (below) so kids can count instead of reading algebra

Script tips for little kids: short sentences, a tiny story with names, pictures to count, one idea per scene,
and say the numbers in words ("four and eight is twelve").

## Make your own quiz (easiest way)
1. Run `python new_quiz.py`
2. Type your question, the answer, an optional common wrong answer, a title, and `vertical` or `wide`
   (press Enter to accept the `[default]`).
3. It writes `quizzes/<name>.json` with a title, a think-about-it countdown and the answer.
4. Run `python make_video.py quizzes/<name>.json`
5. Want more? Open the JSON and add steps from the list below (or ask Claude: "add steps to
   quizzes/<name>.json that draw ...").

## Quiz file settings
| Key | Meaning |
| --- | --- |
| `voice` | e.g. `en-US-AndrewNeural`, `en-IN-NeerjaNeural`, `en-GB-RyanNeural` |
| `aspect` | `vertical` (Shorts/Reels, 1080x1920) or `wide` (YouTube, 16:9) |
| `quality` | Manim quality: `l`, `m`, `h` (`m` is fine for vertical; use `h` for sharp wide video) |
| `captions` | `true` (default) burns the narration into the video as captions; `false` turns them off |
| `music` | optional path to an audio file (mp3/wav), looped quietly under the voice and faded out at the end. If missing it is skipped |
| `music_volume` | optional, default `0.12` (the voice is `1.0`) |

Each scene has a `narration` and a list of `steps`. Steps appear in order, spread over the narration.
Any step can have `"at": 2.5` to appear 2.5 seconds into that scene's narration.
Colors: red, green, yellow, blue, orange, white.

## Step types
Text:
- `{"do": "title", "text": "...", "color": "yellow"}` big bold heading
- `{"do": "text", "text": "..."}` normal line
- `{"do": "math", "tex": "x^2 = 4", "plain": "x² = 4"}` real LaTeX equation (`plain` is the fallback if LaTeX is missing)
- `{"do": "box"}` draws a yellow box around the previous step
- `{"do": "pause", "secs": 1}` wait

Visuals (new):
- `{"do": "shape", "kind": "circle|square|rectangle|triangle", "sides": ["3", "4", "?"], "text": "inside label", "color": "blue"}`
  `sides` are labels: circle = radius; square/rectangle = width, height; triangle (right-angled) = base, height, hypotenuse.
- `{"do": "bars", "values": [33, 67], "labels": ["Stay", "Switch"], "colors": ["red", "green"]}` bar chart
- `{"do": "numberline", "range": [0, 10], "marks": [{"at": 5, "label": "x", "color": "green"}], "jumps": [[2, 5, "+3"]]}`
  dots with labels, plus optional curved arrows between numbers
- `{"do": "dots", "count": 10, "mark": [0, 1], "per_row": 5, "color": "blue", "mark_color": "red"}` row of circles with some highlighted
- `{"do": "arrow", "from": "Switch", "to": "2 in 3", "text": "optional note", "color": "green"}` two labeled boxes joined by an arrow
- `{"do": "things", "kind": "star|apple|coin|ball|cookie", "count": 10, "per_row": 5, "mark": [6, 7], "mark_color": "pink", "dim": [0], "cross": [1]}`
  counting pictures: ringed (`mark`), faded (`dim`) or crossed-out (`cross`) items by position
- `{"do": "timer", "secs": 5, "text": "Think about it!"}` countdown bar with big seconds, so viewers can guess before the answer

## Background music
Put any royalty-free mp3 in the repo (e.g. `music/calm.mp3`) and add `"music": "music/calm.mp3"` to the quiz file.

## No terminal at all
On GitHub open **Actions -> Render quiz video -> Run workflow**, type a quiz file path, then download
the `quiz-video` file from the finished run.
