"""Manim scene that plays a quiz spec (JSON) prepared by make_video.py."""
import json
import math
import os
import random
import shutil

from manim import *
from manim.utils.rate_functions import ease_out_back

SPEC = json.load(open(os.environ["QUIZ_SPEC"]))
VERTICAL = SPEC.get("aspect", "vertical") == "vertical"
if VERTICAL:
    config.pixel_width, config.pixel_height = 1080, 1920
    config.frame_width, config.frame_height = 6.75, 12.0
HAS_LATEX = shutil.which("latex") is not None
KIDS = SPEC.get("style") == "kids"  # mascot, bright background, sound effects, bouncy pop-ins
COLORS = {"red": RED, "green": GREEN, "yellow": YELLOW, "blue": BLUE_C,
          "orange": ORANGE, "white": WHITE, "pink": "#ff7ac6", "purple": "#b388ff",
          "teal": "#2ec4b6"}
SIZE = {"title": 52, "text": 34, "math": 44}
SIZE = {k: v * ((1.35 if KIDS else 1.15) if VERTICAL else 1.25) for k, v in SIZE.items()}
# The mascot takes a band at the top (vertical) or a column on the left (wide).
MASCOT_H = 2.7 if KIDS and VERTICAL else 0
SIDE = 2.6 if KIDS and not VERTICAL else 0
WIDTH = config.frame_width - 0.8 - SIDE
# Content lives above the caption strip at the bottom of the frame.
CAPTIONS = SPEC.get("captions", True)
STRIP = (2.8 if VERTICAL else 1.5) if CAPTIONS else 0.4
REGION_H = config.frame_height - STRIP - 0.4 - MASCOT_H
REGION_X = SIDE / 2
REGION_Y = (STRIP - 0.4 - MASCOT_H) / 2
VIS_H = (4.2 if KIDS else 3.2) if VERTICAL else 2.4  # max height of a drawn visual


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


def make_thing(kind):
    """One small picture-object, drawn from shapes (no emoji fonts needed)."""
    if kind == "apple":
        body = Circle(radius=0.3, color="#ef476f", fill_opacity=1, stroke_width=2)
        stem = Line([0, 0.27, 0], [0, 0.42, 0], color="#7b4a1e", stroke_width=3)
        leaf = Ellipse(width=0.2, height=0.1, color="#52b788", fill_opacity=1, stroke_width=0)
        return VGroup(body, stem, leaf.rotate(PI / 6).move_to([0.1, 0.38, 0]))
    if kind == "coin":
        return VGroup(Circle(radius=0.3, color="#ffd23f", fill_opacity=1, stroke_width=2),
                      Circle(radius=0.2, color="#e0a800", stroke_width=3))
    if kind == "ball":
        return VGroup(Circle(radius=0.3, color="#4cc9f0", fill_opacity=1, stroke_width=2),
                      Circle(radius=0.07, color=WHITE, fill_opacity=0.9, stroke_width=0).move_to([-0.1, 0.12, 0]))
    if kind == "cookie":
        cookie = VGroup(Circle(radius=0.3, color="#d9a066", fill_opacity=1, stroke_width=2))
        for x, y in [(-0.1, 0.1), (0.12, 0.05), (0, -0.14), (-0.14, -0.08)]:
            cookie.add(Dot([x, y, 0], radius=0.045, color="#5a3418"))
        return cookie
    return Star(n=5, outer_radius=0.34, inner_radius=0.15, color="#ffd23f", fill_opacity=1, stroke_width=2)


def make_things(step):
    """Counting picture: `count` objects, some ringed (mark), faded (dim) or crossed out (cross)."""
    kind, count = step.get("kind", "star"), step["count"]
    marked, dimmed, crossed = (set(step.get(k, [])) for k in ("mark", "dim", "cross"))
    hot = col(step, "mark_color", "red")
    things = VGroup()
    for i in range(count):
        t = make_thing(kind)
        if i in marked:
            t.add(Circle(radius=0.42, color=hot, stroke_width=4))
        if i in crossed:
            t.add(Line([-0.3, 0.3, 0], [0.3, -0.3, 0], color=RED, stroke_width=6),
                  Line([-0.3, -0.3, 0], [0.3, 0.3, 0], color=RED, stroke_width=6))
        if i in dimmed:
            t.set_opacity(0.25)
        things.add(t)
    things.arrange_in_grid(cols=min(step.get("per_row", 5), count), buff=0.3)
    return things


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
           "dots": make_dots, "arrow": make_arrow, "things": make_things}


def build_background():
    """Gradient backdrop with soft bubbles drifting upward."""
    w, h = config.frame_width + 0.4, config.frame_height + 0.4
    bg = Rectangle(width=w, height=h, stroke_width=0)
    bg.set_fill(["#1d2b64", "#5b2a9b"], opacity=1)
    bg.set_z_index(-20)
    rng = random.Random(7)
    bubbles = VGroup()
    speeds = []
    for _ in range(12):
        r = rng.uniform(0.15, 0.5)
        b = Circle(radius=r, color=rng.choice(["#ff7ac6", "#4cc9f0", "#ffd23f", "#b388ff"]),
                   fill_opacity=rng.uniform(0.08, 0.2), stroke_width=0)
        b.move_to([rng.uniform(-w / 2, w / 2), rng.uniform(-h / 2, h / 2), 0])
        bubbles.add(b)
        speeds.append(rng.uniform(0.15, 0.4))

    def drift(group, dt):
        for b, v in zip(group, speeds):
            b.shift(UP * v * dt)
            if b.get_bottom()[1] > h / 2:
                b.move_to([b.get_x(), -h / 2 - b.height / 2, 0])
    bubbles.add_updater(drift)
    bubbles.set_z_index(-10)
    return VGroup(bg, bubbles)


def build_buddy():
    """A round friendly mascot. Returns (group, mouth, lids, open-mouth, closed-mouth)."""
    skin, dark = "#ffcf33", "#4a2c0a"
    parts = VGroup()
    for x in (-0.6, 0.6):
        parts.add(Circle(radius=0.25, color="#ffb703", fill_color=skin, fill_opacity=1,
                         stroke_width=3).move_to([x, 0.68, 0]))
    parts.add(Circle(radius=0.8, color="#ffb703", fill_color=skin, fill_opacity=1, stroke_width=4))
    for x in (-0.5, 0.5):
        parts.add(Circle(radius=0.13, color="#ff7ac6", fill_opacity=0.55, stroke_width=0).move_to([x, -0.1, 0]))
    lids = VGroup()
    for x in (-0.3, 0.3):
        parts.add(Circle(radius=0.19, color=WHITE, fill_opacity=1, stroke_width=0).move_to([x, 0.18, 0]))
        parts.add(Circle(radius=0.1, color=dark, fill_opacity=1, stroke_width=0).move_to([x, 0.16, 0]))
        parts.add(Circle(radius=0.035, color=WHITE, fill_opacity=1, stroke_width=0).move_to([x + 0.04, 0.2, 0]))
        lid = Circle(radius=0.21, color=skin, fill_opacity=0, stroke_width=0).move_to([x, 0.18, 0])
        lids.add(lid)
        parts.add(lid)
    closed = Arc(radius=0.24, start_angle=PI * 1.15, angle=PI * 0.7, color=dark, stroke_width=4)
    opened = Ellipse(width=0.34, height=0.3, color="#7a1d2b", fill_opacity=1, stroke_width=3)
    mouth = closed.copy().move_to([0, -0.28, 0])
    parts.add(mouth)
    return parts, mouth, lids, opened, closed


def confetti(scene):
    """A burst of falling paper bits for the big reveal."""
    rng = random.Random(3)
    w, h = config.frame_width, config.frame_height
    pieces, vel = VGroup(), []
    for _ in range(50):
        p = Rectangle(width=0.16, height=0.09, color=rng.choice(["#ff7ac6", "#4cc9f0", "#ffd23f", "#52b788", "#ef476f"]),
                      fill_opacity=1, stroke_width=0)
        p.rotate(rng.uniform(0, TAU)).move_to([rng.uniform(-w / 2, w / 2), h / 2 + rng.uniform(0, 1.5), 0])
        pieces.add(p)
        vel.append((rng.uniform(-0.4, 0.4), rng.uniform(-3.2, -5.5), rng.uniform(-5, 5)))
    age = [0.0]

    def fall(group, dt):
        age[0] += dt
        for p, (vx, vy, spin) in zip(group, vel):
            p.shift([vx * dt, vy * dt, 0])
            p.rotate(spin * dt)
        if age[0] > 3.5:
            group.clear_updaters()
            scene.remove(group)
    pieces.add_updater(fall)
    pieces.set_z_index(30)
    scene.add(pieces)


class QuizScene(Scene):
    def wait_until(self, t):
        if t - self.time > 0.05:
            self.wait(t - self.time)

    def sfx(self, name):
        if KIDS:
            self.events.append((self.time, name))

    def countdown(self, group, secs):
        head, number, back, bar = group
        full = back.width
        tracker = ValueTracker(secs)
        number.add_updater(lambda n: n.become(
            Text(str(math.ceil(tracker.get_value())), font_size=96, color=ORANGE).move_to(n)))
        bar.add_updater(lambda b: b.stretch_to_fit_width(
            max(0.01, full * tracker.get_value() / secs)).align_to(back, LEFT))
        self.play(FadeIn(group), run_time=0.4)
        left = secs
        while left > 0:  # one tick per second
            self.sfx("tick")
            chunk = min(1, left)
            left -= chunk
            self.play(tracker.animate.set_value(left), run_time=chunk, rate_func=linear)
        self.sfx("ding")
        number.clear_updaters()
        bar.clear_updaters()

    def add_buddy(self):
        """Mascot that bobs, blinks, hops on celebrations and moves its mouth while narration plays."""
        buddy, mouth, lids, opened, closed = build_buddy()
        if VERTICAL:
            base = np.array([0, config.frame_height / 2 - 1.6, 0])
            buddy.scale(1.3)
        else:
            base = np.array([-config.frame_width / 2 + 1.5, 0.6, 0])
            buddy.scale(1.25)
        buddy.move_to(base)
        self.windows, self.hop = [], -9.0
        shown = [None]

        def alive(m):
            t = self.time
            hop = 0.45 * abs(math.sin(2 * PI * (t - self.hop) / 0.9)) if 0 <= t - self.hop < 0.9 else 0
            m.move_to(base + UP * (0.05 * math.sin(t * 3) + hop))
            talking = any(a <= t <= b for a, b in self.windows) and math.sin(t * 18) > -0.3
            if talking != shown[0]:
                shown[0] = talking
                mouth.become((opened if talking else closed).copy().move_to(mouth.get_center()))
            for lid in lids:
                lid.set_fill(opacity=1 if t % 3.4 < 0.13 else 0)
        buddy.set_z_index(5)
        self.play(GrowFromCenter(buddy), run_time=0.6, rate_func=ease_out_back)
        buddy.add_updater(alive)

    def construct(self):
        self.camera.background_color = "#14161f"
        self.events = []  # (time, sound effect name), mixed in by make_video.py
        if KIDS:
            self.add(build_background())
            self.add_buddy()
        starts = []
        for sc in SPEC["scenes"]:
            start = self.time
            starts.append(start)
            if KIDS:
                self.windows += [(start + a, start + b + 0.1) for a, b, _ in sc["sentences"]]
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
                items.move_to([REGION_X, REGION_Y, 0])
                if kind != "timer" and step.get("sfx", "pop") != "none":
                    self.sfx(step.get("sfx", "pop"))
                if step.get("celebrate"):
                    self.sfx("tada")
                    self.hop = self.time
                    confetti(self)
                if kind == "timer":
                    self.countdown(m, secs)
                elif KIDS:  # bouncy pop-in
                    self.play(GrowFromCenter(m), run_time=step.get("secs", 0.7), rate_func=ease_out_back)
                elif kind in ("title", *VISUALS):
                    self.play(FadeIn(m, shift=UP * 0.3), run_time=step.get("secs", 1.0))
                else:
                    self.play(Write(m), run_time=step.get("secs", 1.2))
            self.wait_until(start + sc["duration"])
            self.play(FadeOut(VGroup(items, extras)), run_time=0.4)
        with open(os.environ["QUIZ_TIMES"], "w") as f:
            json.dump({"starts": starts, "total": self.time, "events": self.events}, f)
