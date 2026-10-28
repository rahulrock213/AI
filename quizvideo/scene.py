"""Manim scene that plays a quiz spec (JSON) prepared by make_video.py."""
import json
import math
import os
import shutil

from manim import *

SPEC = json.load(open(os.environ["QUIZ_SPEC"]))
VERTICAL = SPEC.get("aspect", "vertical") == "vertical"
if VERTICAL:
    config.pixel_width, config.pixel_height = 1080, 1920
    config.frame_width, config.frame_height = 6.75, 12.0
HAS_LATEX = shutil.which("latex") is not None
COLORS = {"red": RED, "green": GREEN, "yellow": YELLOW, "blue": BLUE_C,
          "orange": ORANGE, "white": WHITE}
SIZE = {"title": 52, "text": 34, "math": 44}
SIZE = {k: v * (1.15 if VERTICAL else 1.25) for k, v in SIZE.items()}
WIDTH = config.frame_width - 0.8
# Content lives above the caption strip at the bottom of the frame.
CAPTIONS = SPEC.get("captions", True)
STRIP = (2.8 if VERTICAL else 1.5) if CAPTIONS else 0.4
REGION_H = config.frame_height - STRIP - 0.4
REGION_Y = (STRIP - 0.4) / 2
VIS_H = 3.2 if VERTICAL else 2.4  # max height of a drawn visual


def col(step, key="color", default="white"):
    return COLORS.get(step.get(key, default), WHITE)


def fit(m, height=None):
    if m.width > WIDTH:
        m.scale_to_fit_width(WIDTH)
    if height and m.height > height:
        m.scale_to_fit_height(height)
    return m


def label(text, color=WHITE, size=28):
    return Text(str(text), font_size=size, color=color)


def make_shape(step):
    kind, color = step.get("kind", "circle"), col(step)
    sides = step.get("sides", [])
    style = dict(color=color, fill_color=color, fill_opacity=0.25, stroke_width=5)
    if kind == "circle":
        shape = Circle(radius=1.2, **style)
        parts = [shape]
        if sides:  # radius line with a label
            line = Line(shape.get_center(), shape.get_right(), color=WHITE, stroke_width=4)
            parts += [line, label(sides[0]).next_to(line, UP, buff=0.1)]
    elif kind in ("square", "rectangle"):
        w, h = (2.4, 2.4) if kind == "square" else (3.2, 1.8)
        shape = Rectangle(width=w, height=h, **style)
        parts = [shape]
        if sides:
            parts.append(label(sides[0]).next_to(shape, DOWN, buff=0.15))
            parts.append(label(sides[-1]).next_to(shape, RIGHT, buff=0.15))
    elif kind == "triangle":  # right triangle: base, height, hypotenuse
        shape = Polygon([0, 0, 0], [3, 0, 0], [0, 2, 0], **style)
        corner = Polygon([0, 0, 0], [0.3, 0, 0], [0.3, 0.3, 0], [0, 0.3, 0],
                         color=WHITE, stroke_width=3)
        parts = [shape, corner]
        if sides:
            parts.append(label(sides[0]).next_to(shape, DOWN, buff=0.15))
            parts.append(label(sides[1]).next_to(shape, LEFT, buff=0.15))
            parts.append(label(sides[2]).move_to(shape.get_center() + [0.8, 0.7, 0]))
    else:
        raise ValueError(f"unknown shape kind: {kind}")
    if step.get("text"):  # caption inside the shape
        parts.append(label(step["text"], WHITE, 32).move_to(shape.get_center()))
    return VGroup(*parts)


def make_bars(step):
    values = step["values"]
    labels = step.get("labels", [""] * len(values))
    colors = step.get("colors", [step.get("color", "blue")] * len(values))
    top = max(values) or 1
    bars = VGroup()
    for v, name, c in zip(values, labels, colors):
        bar = Rectangle(width=0.9, height=max(0.05, 2.4 * v / top), color=COLORS.get(c, BLUE_C),
                        fill_opacity=0.8, stroke_width=2)
        bar.align_to(ORIGIN, DOWN)
        bars.add(VGroup(bar, label(v).next_to(bar, UP, buff=0.1)))
    bars.arrange(RIGHT, buff=0.5, aligned_edge=DOWN)
    for g, name in zip(bars, labels):
        g.add(label(name).next_to(g[0], DOWN, buff=0.15))
    return bars


def make_numberline(step):
    lo, hi = step.get("range", [0, 10])
    length = WIDTH - 0.6
    x = lambda v: (v - lo) / (hi - lo) * length - length / 2
    parts = [Line([x(lo), 0, 0], [x(hi), 0, 0], color=WHITE, stroke_width=4)]
    ticks = [lo, hi] if hi - lo > 12 else range(lo, hi + 1)
    for t in ticks:
        parts.append(Line([x(t), -0.12, 0], [x(t), 0.12, 0], color=WHITE, stroke_width=3))
        parts.append(label(t, size=24).move_to([x(t), -0.4, 0]))
    below = bool(step.get("jumps"))  # keep mark labels clear of the jump arcs
    for i, mark in enumerate(step.get("marks", [])):
        c = COLORS.get(mark.get("color", "yellow"), YELLOW)
        parts.append(Dot([x(mark["at"]), 0, 0], color=c, radius=0.14))
        if "label" in mark:
            y = 0.5 + 0.5 * (i % 2)  # neighbouring labels sit at different heights
            parts.append(label(mark["label"], c).move_to([x(mark["at"]), -(y + 0.35) if below else y, 0]))
    for a, b, text in step.get("jumps", []):  # arcs such as [0, 3, "+3"]
        arc = CurvedArrow([x(a), 0.2, 0], [x(b), 0.2, 0], angle=-1.2, color=ORANGE, stroke_width=4)
        parts.append(arc)
        parts.append(label(text, ORANGE).move_to([(x(a) + x(b)) / 2, 0.2 + abs(x(b) - x(a)) * 0.3 + 0.35, 0]))
    return VGroup(*parts)


def make_dots(step):
    count, per_row = step["count"], step.get("per_row", 5)
    marked = set(step.get("mark", []))
    base, hot = col(step, "color", "blue"), col(step, "mark_color", "red")
    dots = VGroup(*[Circle(radius=0.28, color=hot if i in marked else base, fill_opacity=0.8,
                           stroke_width=2) for i in range(count)])
    dots.arrange_in_grid(cols=min(per_row, count), buff=0.25)
    return dots


def make_arrow(step):
    def box(text, color):
        t = label(text, color, 32)
        return VGroup(RoundedRectangle(corner_radius=0.15, width=t.width + 0.5, height=t.height + 0.4,
                                       color=color), t)
    left, right = box(step["from"], col(step, "from_color")), box(step["to"], col(step, "color", "green"))
    arrow = Arrow(LEFT, RIGHT, buff=0, color=WHITE).set_width(1.4)
    row = VGroup(left, arrow, right).arrange(RIGHT, buff=0.2)
    if step.get("text"):
        row.add(label(step["text"], YELLOW, 24).next_to(arrow, UP, buff=0.1))
    return row


def make_timer(step):
    """Think-about-it countdown: a shrinking bar with the seconds left."""
    secs = step.get("secs", 5)
    back = RoundedRectangle(corner_radius=0.2, width=WIDTH - 1, height=0.4, color=WHITE, stroke_width=3)
    bar = Rectangle(width=back.width, height=0.4, color=ORANGE, fill_opacity=1, stroke_width=0)
    bar.move_to(back)
    left = Text(str(secs), font_size=96, color=ORANGE)
    head = label(step.get("text", "Think about it!"), YELLOW, 40)
    group = VGroup(head, left, back, bar)
    group.arrange(DOWN, buff=0.3)
    bar.move_to(back)
    return group, secs


def make(step):
    kind = step["do"]
    color = col(step)
    if kind == "math" and HAS_LATEX:
        m = MathTex(step["tex"], font_size=SIZE["math"], color=color)
    elif kind == "math":
        m = Text(step.get("plain", step["tex"]), font_size=SIZE["text"], color=color)
    elif kind in VISUALS:
        return fit(VISUALS[kind](step), VIS_H)
    else:
        m = Text(step["text"], font_size=SIZE.get(kind, SIZE["text"]), color=color,
                 weight=BOLD if kind == "title" else NORMAL, line_spacing=1.1)
    return fit(m)


VISUALS = {"shape": make_shape, "bars": make_bars, "numberline": make_numberline,
           "dots": make_dots, "arrow": make_arrow}


class QuizScene(Scene):
    def wait_until(self, t):
        if t - self.time > 0.05:
            self.wait(t - self.time)

    def countdown(self, group, secs):
        head, number, back, bar = group
        full = back.width
        tracker = ValueTracker(secs)
        number.add_updater(lambda n: n.become(
            Text(str(math.ceil(tracker.get_value())), font_size=96, color=ORANGE).move_to(n)))
        bar.add_updater(lambda b: b.stretch_to_fit_width(
            max(0.01, full * tracker.get_value() / secs)).align_to(back, LEFT))
        self.play(FadeIn(group), run_time=0.4)
        self.play(tracker.animate.set_value(0), run_time=secs, rate_func=linear)
        number.clear_updaters()
        bar.clear_updaters()

    def construct(self):
        self.camera.background_color = "#14161f"
        starts = []
        for sc in SPEC["scenes"]:
            start = self.time
            starts.append(start)
            avail = sc["duration"] - 0.4
            shown = [s for s in sc["steps"] if s["do"] != "box"]
            items, extras = VGroup(), VGroup()
            seen = 0
            for step in sc["steps"]:
                kind = step["do"]
                if kind == "box":
                    if len(items):
                        # follows its item so later steps can re-arrange the group
                        box = SurroundingRectangle(items[-1], color=YELLOW, buff=0.15)
                        box.add_updater(lambda b, t=items[-1]: b.move_to(t))
                        self.play(Create(box), run_time=0.8)
                        extras.add(box)
                    continue
                # spread steps over the narration unless the step says "at": seconds
                self.wait_until(start + step.get("at", seen * avail / len(shown)))
                seen += 1
                if kind == "pause":
                    self.wait(step.get("secs", 1))
                    continue
                if kind == "timer":
                    m, secs = make_timer(step)
                else:
                    m = make(step)
                items.add(m)
                items.arrange(DOWN, buff=0.45)
                if items.height > REGION_H:
                    items.scale_to_fit_height(REGION_H)
                items.move_to([0, REGION_Y, 0])
                if kind == "timer":
                    self.countdown(m, secs)
                elif kind in ("title", *VISUALS):
                    self.play(FadeIn(m, shift=UP * 0.3), run_time=step.get("secs", 1.0))
                else:
                    self.play(Write(m), run_time=step.get("secs", 1.2))
            self.wait_until(start + sc["duration"])
            self.play(FadeOut(VGroup(items, extras)), run_time=0.4)
        with open(os.environ["QUIZ_TIMES"], "w") as f:
            json.dump({"starts": starts, "total": self.time}, f)
