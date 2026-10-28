"""Manim scene that plays a quiz spec (JSON) prepared by make_video.py."""
import json
import os
import shutil

from manim import *

SPEC = json.load(open(os.environ["QUIZ_SPEC"]))
if SPEC.get("aspect", "vertical") == "vertical":
    config.pixel_width, config.pixel_height = 1080, 1920
    config.frame_width, config.frame_height = 6.75, 12.0
HAS_LATEX = shutil.which("latex") is not None
COLORS = {"red": RED, "green": GREEN, "yellow": YELLOW, "blue": BLUE_C,
          "orange": ORANGE, "white": WHITE}
SIZE = {"title": 52, "text": 34, "math": 44}
WIDTH = config.frame_width - 0.8


def fit(m):
    if m.width > WIDTH:
        m.scale_to_fit_width(WIDTH)
    return m


def make(step):
    kind = step["do"]
    color = COLORS.get(step.get("color", "white"), WHITE)
    if kind == "math" and HAS_LATEX:
        m = MathTex(step["tex"], font_size=SIZE["math"], color=color)
    elif kind == "math":
        m = Text(step.get("plain", step["tex"]), font_size=SIZE["text"], color=color)
    else:
        m = Text(step["text"], font_size=SIZE.get(kind, 34), color=color,
                 weight=BOLD if kind == "title" else NORMAL, line_spacing=1.1)
    return fit(m)


class QuizScene(Scene):
    def construct(self):
        self.camera.background_color = "#14161f"
        for sc in SPEC["scenes"]:
            self.add_sound(sc["audio"])
            start = self.renderer.time
            items = VGroup()
            for step in sc["steps"]:
                kind = step["do"]
                if kind == "pause":
                    self.wait(step.get("secs", 1))
                    continue
                if kind == "box":
                    if len(items):
                        box = SurroundingRectangle(items[-1], color=YELLOW, buff=0.15)
                        self.play(Create(box), run_time=0.8)
                        items.add(box)
                    continue
                m = make(step)
                items.add(m)
                items.arrange(DOWN, buff=0.45).move_to(ORIGIN)
                self.play(Write(m) if kind != "title" else FadeIn(m, shift=UP * 0.3),
                          run_time=step.get("secs", 1.2))
            self.wait(max(0.3, sc["duration"] - (self.renderer.time - start)))
            self.play(FadeOut(items), run_time=0.4)
