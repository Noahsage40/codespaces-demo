"""Small motion-graphics engine: draws each frame with Pillow and pipes it to ffmpeg.

Every element appears on a *cue*: a phrase from the scene's narration. The cue time
comes from ElevenLabs character timings when available, otherwise from the
phrase's position in the text scaled to the audio length.
"""
import math
import random
import subprocess
from functools import lru_cache

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS = 1920, 1080, 30
LEAD, TAIL = 0.25, 0.45  # silence before / after each scene's narration

INK = (11, 14, 19)
PANEL = (22, 27, 36)
LINE = (44, 52, 66)
WHITE = (244, 246, 249)
MUTED = (142, 152, 168)
YELLOW = (255, 200, 40)
RED = (255, 72, 72)
GREEN = (52, 214, 128)
BLUE = (80, 160, 255)

FONT_DIR = "/usr/share/fonts/opentype/inter/"


@lru_cache(maxsize=None)
def font(size, weight="Black"):
    if weight == "glyph":
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size)
    return ImageFont.truetype(f"{FONT_DIR}InterDisplay-{weight}.otf", size)


def clamp(v, a=0.0, b=1.0):
    return a if v < a else b if v > b else v


def ease_out(p):
    return 1 - (1 - p) ** 3


def ease_inout(p):
    return 4 * p ** 3 if p < 0.5 else 1 - (-2 * p + 2) ** 3 / 2


def ease_back(p):
    c1, c3 = 1.9, 2.9
    return 1 + c3 * (p - 1) ** 3 + c1 * (p - 1) ** 2


def lerp(a, b, p):
    return a + (b - a) * p


def with_alpha(img, k):
    if k >= 0.999:
        return img
    a = img.getchannel("A").point(lambda v: int(v * k))
    out = img.copy()
    out.putalpha(a)
    return out


# --------------------------------------------------------------------------- timing
class Timer:
    """Turns cues into seconds. A cue is a phrase, a number of seconds, or (cue, offset)."""

    def __init__(self, text, audio_dur, alignment=None, fixed=None):
        self.text = text or ""
        self.low = self.text.lower()
        self.audio_dur = audio_dur
        self.alignment = alignment
        self.duration = fixed if fixed else LEAD + audio_dur + TAIL

    def __call__(self, cue):
        if cue is None:
            return 0.0
        if isinstance(cue, (int, float)):
            return float(cue) if cue >= 0 else self.duration + cue
        if isinstance(cue, tuple):
            return self(cue[0]) + cue[1]
        if cue == "end":
            return LEAD + self.audio_dur
        idx = self.low.find(cue.lower())
        if idx < 0:
            raise ValueError(f"cue not found in narration: {cue!r}")
        if self.alignment and len(self.alignment["chars"]) == len(self.text):
            return LEAD + self.alignment["starts"][idx]
        return LEAD + idx / max(1, len(self.text)) * self.audio_dur


# --------------------------------------------------------------------------- elements
class El:
    anim_dur = 0.45
    sfx = None

    def __init__(self, at=0, out=None, anim="rise"):
        self.at, self.out, self.anim = at, out, anim

    def resolve(self, T):
        self.t0 = T(self.at)
        self.t1 = T(self.out) if self.out is not None else None

    def alpha_offset(self, t):
        """Returns (opacity, dx, dy, scale) for the entry/exit animation."""
        p = clamp((t - self.t0) / self.anim_dur)
        k, dx, dy, sc = 1.0, 0, 0, 1.0
        if self.anim == "rise":
            e = ease_out(p)
            k, dy = e, (1 - e) * 40
        elif self.anim == "pop":
            k = clamp(p * 3)
            sc = lerp(0.6, 1.0, ease_back(p))
        elif self.anim == "fade":
            k = ease_out(p)
        elif self.anim == "left":
            e = ease_out(p)
            k, dx = e, (e - 1) * 80
        elif self.anim == "right":
            e = ease_out(p)
            k, dx = e, (1 - e) * 80
        if self.t1 is not None:
            q = clamp((t - self.t1) / 0.3)
            k *= 1 - q
        return k, dx, dy, sc

    def visible(self, t):
        if t < self.t0:
            return False
        return self.t1 is None or t < self.t1 + 0.3

    def draw(self, frame, t, T):
        raise NotImplementedError


def place(sprite, x, y, anchor):
    w, h = sprite.size
    ax = {"l": 0, "m": w / 2, "r": w}[anchor[0]]
    ay = {"t": 0, "m": h / 2, "b": h}[anchor[1]]
    return x - ax, y - ay


def paste(frame, sprite, x, y, anchor, k, dx, dy, sc):
    if sc != 1.0:
        sw, sh = max(1, int(sprite.width * sc)), max(1, int(sprite.height * sc))
        cx, cy = place(sprite, x, y, anchor)
        cx, cy = cx + sprite.width / 2, cy + sprite.height / 2
        sprite = sprite.resize((sw, sh), Image.BILINEAR)
        px, py = cx - sw / 2, cy - sh / 2
    else:
        px, py = place(sprite, x, y, anchor)
    frame.alpha_composite(with_alpha(sprite, k), (int(px + dx), int(py + dy)))


def wrap(text, f, maxw):
    lines = []
    for para in text.split("\n"):
        cur = ""
        for word in para.split(" "):
            test = (cur + " " + word).strip()
            if maxw and f.getlength(test) > maxw and cur:
                lines.append(cur)
                cur = word
            else:
                cur = test
        lines.append(cur)
    return lines


@lru_cache(maxsize=512)
def text_sprite(text, size, weight, color, maxw, align, bg, pad, radius, shadow, spacing, outline):
    f = font(size, weight)
    lines = wrap(text, f, maxw)
    asc, desc = f.getmetrics()
    lh = int((asc + desc) * spacing)
    tw = int(max(f.getlength(l) for l in lines)) if lines else 0
    th = lh * (len(lines) - 1) + asc + desc
    px, py = pad
    sh = 18 if shadow else 0
    w, h = tw + 2 * px + 2 * sh, th + 2 * py + 2 * sh
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    if shadow:
        s = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        sd = ImageDraw.Draw(s)
        if bg:
            sd.rounded_rectangle([sh, sh + 8, w - sh, h - sh + 8], radius, fill=(0, 0, 0, 150))
        else:
            for i, l in enumerate(lines):
                lx = sh + px + (tw - f.getlength(l)) * {"left": 0, "center": 0.5, "right": 1}[align]
                sd.text((lx, sh + py + i * lh + 5), l, font=f, fill=(0, 0, 0, 200))
        img = Image.alpha_composite(img, s.filter(ImageFilter.GaussianBlur(9)))
    d = ImageDraw.Draw(img)
    if bg:
        d.rounded_rectangle([sh, sh, w - sh, h - sh], radius, fill=bg + (255,) if len(bg) == 3 else bg,
                            outline=outline, width=3 if outline else 0)
    for i, l in enumerate(lines):
        lx = sh + px + (tw - f.getlength(l)) * {"left": 0, "center": 0.5, "right": 1}[align]
        d.text((lx, sh + py + i * lh), l, font=f, fill=color)
    return img, sh


class Text(El):
    def __init__(self, text, x, y, size=64, weight="Black", color=WHITE, anchor="mm", maxw=None,
                 align="center", bg=None, pad=(0, 0), radius=14, shadow=True, spacing=1.12,
                 outline=None, sfx=None, **kw):
        super().__init__(**kw)
        self.args = (text, size, weight, color, maxw, align, bg, pad, radius, shadow, spacing, outline)
        self.x, self.y, self.anchor, self.sfx = x, y, anchor, sfx

    def draw(self, frame, t, T):
        spr, sh = text_sprite(*self.args)
        k, dx, dy, sc = self.alpha_offset(t)
        ax = {"l": -sh, "m": 0, "r": sh}[self.anchor[0]]
        ay = {"t": -sh, "m": 0, "b": sh}[self.anchor[1]]
        paste(frame, spr, self.x + ax, self.y + ay, self.anchor, k, dx, dy, sc)


class Rect(El):
    """Panel / bar. grow='up' or 'right' animates the size; otherwise uses the entry animation."""

    def __init__(self, x, y, w, h, fill=PANEL, outline=None, width=3, radius=18, grow=None,
                 grow_dur=0.7, shadow=True, **kw):
        super().__init__(**kw)
        self.box = (x, y, w, h)
        self.fill, self.outline, self.width, self.radius = fill, outline, width, radius
        self.grow, self.grow_dur, self.shadow = grow, grow_dur, shadow
        if grow:
            self.anim = "fade"
            self.anim_dur = 0.15

    def draw(self, frame, t, T):
        x, y, w, h = self.box
        k, dx, dy, sc = self.alpha_offset(t)
        if self.grow:
            p = ease_out(clamp((t - self.t0) / self.grow_dur))
            if self.grow == "up":
                y, h = y + h * (1 - p), h * p
            else:
                w = w * p
        if w < 2 or h < 2:
            return
        layer = Image.new("RGBA", (int(w) + 80, int(h) + 80), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        r = min(self.radius, int(min(w, h) / 2))
        if self.shadow:
            d.rounded_rectangle([40, 52, 40 + w, 52 + h], r, fill=(0, 0, 0, 110))
            layer = layer.filter(ImageFilter.GaussianBlur(14))
            d = ImageDraw.Draw(layer)
        fill = self.fill if len(self.fill) == 4 else self.fill + (255,)
        d.rounded_rectangle([40, 40, 40 + w, 40 + h], r, fill=fill,
                            outline=self.outline, width=self.width if self.outline else 0)
        frame.alpha_composite(with_alpha(layer, k), (int(x - 40 + dx), int(y - 40 + dy)))


class Counter(El):
    def __init__(self, x, y, to, fmt, frm=0, dur=1.3, size=150, color=WHITE, anchor="mm",
                 weight="Black", **kw):
        kw.setdefault("anim", "pop")
        super().__init__(**kw)
        self.x, self.y, self.to, self.frm, self.fmt, self.dur = x, y, to, frm, fmt, dur
        self.size, self.color, self.anchor, self.weight = size, color, anchor, weight

    def draw(self, frame, t, T):
        p = ease_out(clamp((t - self.t0) / self.dur))
        v = lerp(self.frm, self.to, p)
        spr, sh = text_sprite(self.fmt(v), self.size, self.weight, self.color, None, "center",
                              None, (0, 0), 0, True, 1.1, None)
        k, dx, dy, sc = self.alpha_offset(t)
        ax = {"l": -sh, "m": 0, "r": sh}[self.anchor[0]]
        paste(frame, spr, self.x + ax, self.y, self.anchor, k, dx, dy, sc)


class Stamp(El):
    """A rotated, outlined stamp that slams in and shakes the camera."""
    sfx = "hit"

    def __init__(self, text, x, y, color=RED, size=92, angle=-7, **kw):
        kw.setdefault("anim", "slam")
        super().__init__(**kw)
        self.text, self.x, self.y, self.color, self.size, self.angle = text, x, y, color, size, angle
        self.shake = True

    @property
    def sprite(self):
        if not hasattr(self, "_spr"):
            f = font(self.size, "Black")
            tw = int(f.getlength(self.text))
            asc, desc = f.getmetrics()
            pad = 34
            img = Image.new("RGBA", (tw + 2 * pad + 40, asc + desc + 2 * pad), (0, 0, 0, 0))
            d = ImageDraw.Draw(img)
            d.rounded_rectangle([20, 8, img.width - 20, img.height - 8], 14,
                                fill=(0, 0, 0, 120), outline=self.color, width=9)
            d.text((20 + pad, pad), self.text, font=f, fill=self.color)
            self._spr = img.rotate(self.angle, expand=True, resample=Image.BICUBIC)
        return self._spr

    def alpha_offset(self, t):
        p = clamp((t - self.t0) / 0.22)
        k = clamp(p * 2)
        sc = lerp(2.2, 1.0, ease_out(p))
        if self.t1 is not None:
            k *= 1 - clamp((t - self.t1) / 0.3)
        return k, 0, 0, sc

    def draw(self, frame, t, T):
        k, dx, dy, sc = self.alpha_offset(t)
        paste(frame, self.sprite, self.x, self.y, "mm", k, dx, dy, sc)


class Strike(El):
    """A line wiped on from (x1,y1) to (x2,y2)."""
    sfx = "swipe"

    def __init__(self, x1, y1, x2, y2, color=RED, width=12, dur=0.35, **kw):
        super().__init__(**kw)
        self.p1, self.p2, self.color, self.width, self.dur = (x1, y1), (x2, y2), color, width, dur

    def draw(self, frame, t, T):
        p = ease_out(clamp((t - self.t0) / self.dur))
        k = 1.0 if self.t1 is None else 1 - clamp((t - self.t1) / 0.3)
        (x1, y1), (x2, y2) = self.p1, self.p2
        d = ImageDraw.Draw(frame)
        d.line([x1, y1, lerp(x1, x2, p), lerp(y1, y2, p)], fill=self.color + (int(255 * k),),
               width=self.width)


class Ring(El):
    """Hand-drawn style red circle around a screen-space box."""
    sfx = "swipe"

    def __init__(self, box, color=RED, width=9, dur=0.55, **kw):
        super().__init__(**kw)
        self.box, self.color, self.width, self.dur = box, color, width, dur

    def draw(self, frame, t, T):
        draw_ring(frame, self.box, ease_inout(clamp((t - self.t0) / self.dur)), self.color, self.width)


def draw_ring(frame, box, p, color, width):
    if p <= 0:
        return
    x0, y0, x1, y1 = box
    padx, pady = (x1 - x0) * 0.08 + 18, (y1 - y0) * 0.25 + 16
    d = ImageDraw.Draw(frame)
    # two slightly offset passes for a marker feel
    d.arc([x0 - padx, y0 - pady, x1 + padx, y1 + pady], -200, -200 + 375 * p, fill=color, width=width)
    d.arc([x0 - padx + 6, y0 - pady - 5, x1 + padx - 4, y1 + pady + 3], -195, -195 + 360 * p,
          fill=color, width=max(2, width // 3))


class Shot(El):
    """A screenshot on a floating page. The camera moves to `focus` regions on cue, and marks
    (highlighter sweeps and red rings) are drawn in screenshot coordinates."""

    def __init__(self, path, box=(210, 150, 1500, 844), focus=(), marks=(), dim=False, **kw):
        kw.setdefault("anim", "rise")
        super().__init__(**kw)
        self.path, self.box, self.focus, self.marks = path, box, list(focus), list(marks)
        self.P = 60

    def resolve(self, T):
        super().resolve(T)
        self.focus_t = [(T(c), r) for c, r in self.focus]
        self.marks_t = [(m[0], T(m[1]), m[2], (m[3] if len(m) > 3 else None)) for m in self.marks]

    @property
    def sprite(self):
        if not hasattr(self, "_spr"):
            img = Image.open(self.path).convert("RGBA")
            P = self.P
            spr = Image.new("RGBA", (img.width + 2 * P, img.height + 2 * P), (0, 0, 0, 0))
            sh = Image.new("RGBA", spr.size, (0, 0, 0, 0))
            ImageDraw.Draw(sh).rectangle([P, P + 22, P + img.width, P + img.height + 22], fill=(0, 0, 0, 170))
            spr = Image.alpha_composite(spr, sh.filter(ImageFilter.GaussianBlur(22)))
            spr.paste(img, (P, P))
            ImageDraw.Draw(spr).rectangle([P - 1, P - 1, P + img.width, P + img.height], outline=(255, 255, 255, 70), width=2)
            self._spr, self._src = spr, img.size
        return self._spr

    def fit(self, rect):
        """Transform (scale, ox, oy) that shows source rect (x0,y0,x1,y1) centred, filling ~80%."""
        x0, y0, x1, y1 = rect
        s = min(W * 0.8 / (x1 - x0), H * 0.68 / (y1 - y0))
        cx, cy = (x0 + x1) / 2 + self.P, (y0 + y1) / 2 + self.P
        return s, W / 2 - cx * s, H / 2 + 20 - cy * s

    def transform(self, t):
        spr = self.sprite
        bx, by, bw, bh = self.box
        s0 = bw / self._src[0]
        cur = (s0, bx - self.P * s0, by - self.P * s0)
        for ft, rect in self.focus_t:
            if t < ft:
                break
            target = self.fit(rect) if rect else (s0, bx - self.P * s0, by - self.P * s0)
            p = ease_inout(clamp((t - ft) / 1.1))
            cur = tuple(lerp(a, b, p) for a, b in zip(cur, target))
        return cur

    def draw(self, frame, t, T):
        spr = self.sprite
        s, ox, oy = self.transform(t)
        k, dx, dy, _ = self.alpha_offset(t)
        ox, oy = ox + dx, oy + dy
        # crop only the visible part of the sprite, then scale it: cheap even when zoomed in
        p0x, p0y = max(0.0, -ox / s), max(0.0, -oy / s)
        p1x, p1y = min(spr.width, (W - ox) / s), min(spr.height, (H - oy) / s)
        if p1x <= p0x or p1y <= p0y:
            return
        tw, th = max(1, round((p1x - p0x) * s)), max(1, round((p1y - p0y) * s))
        part = spr.resize((tw, th), Image.BILINEAR, box=(p0x, p0y, p1x, p1y))
        frame.alpha_composite(with_alpha(part, k), (int(round(ox + p0x * s)), int(round(oy + p0y * s))))

        def to_screen(r):
            return (ox + (r[0] + self.P) * s, oy + (r[1] + self.P) * s,
                    ox + (r[2] + self.P) * s, oy + (r[3] + self.P) * s)

        for kind, mt, rect, mout in self.marks_t:
            if t < mt or (mout is not None and t > T(mout)):
                continue
            sx0, sy0, sx1, sy1 = to_screen(rect)
            if kind == "hl":
                p = ease_out(clamp((t - mt) / 0.5))
                hl = Image.new("RGBA", (max(1, int((sx1 - sx0) * p)), max(1, int(sy1 - sy0))), YELLOW + (95,))
                frame.alpha_composite(hl, (int(sx0), int(sy0)))
            elif kind == "ring":
                draw_ring(frame, (sx0, sy0, sx1, sy1), ease_inout(clamp((t - mt) / 0.55)), RED, 9)
            elif kind == "box":
                p = ease_out(clamp((t - mt) / 0.3))
                ImageDraw.Draw(frame).rectangle([sx0, sy0, sx1, sy1], outline=YELLOW + (int(255 * p),), width=6)

    def sfx_times(self):
        out = [(mt, "swipe") for kind, mt, _, _ in self.marks_t if kind in ("hl", "ring")]
        out += [(ft, "whoosh") for ft, _ in self.focus_t]
        return out


# --------------------------------------------------------------------------- background
@lru_cache(maxsize=8)
def background(glow=BLUE):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    base = np.zeros((H, W, 3), np.float32) + np.array(INK, np.float32)
    g = np.exp(-(((xx - W * 0.72) / 900) ** 2 + ((yy - H * 0.2) / 650) ** 2))
    base += g[..., None] * np.array(glow, np.float32) * 0.16
    g2 = np.exp(-(((xx - W * 0.15) / 800) ** 2 + ((yy - H * 0.95) / 500) ** 2))
    base += g2[..., None] * np.array((120, 60, 200), np.float32) * 0.06
    grid = ((xx % 64) < 1.5) | ((yy % 64) < 1.5)
    base += grid[..., None] * 7
    vig = 1 - 0.55 * (((xx - W / 2) / (W * 0.75)) ** 2 + ((yy - H / 2) / (H * 0.75)) ** 2)
    base *= np.clip(vig, 0.35, 1)[..., None]
    return Image.fromarray(np.clip(base, 0, 255).astype(np.uint8)).convert("RGBA")


@lru_cache(maxsize=1)
def grain_frames():
    rng = np.random.default_rng(7)
    return [rng.normal(0, 5.5, (H // 2, W // 2, 1)).astype(np.int16).repeat(2, 0).repeat(2, 1) for _ in range(6)]


# --------------------------------------------------------------------------- scene
class Scene:
    def __init__(self, sid, chapter, text, els=(), src=None, hold=None, glow=BLUE, push=0.045,
                 whip=True):
        self.sid, self.chapter, self.text, self.els = sid, chapter, text, list(els)
        self.src, self.hold, self.glow, self.push, self.whip = src, hold, glow, push, whip

    def setup(self, audio_dur, alignment=None):
        self.T = Timer(self.text, audio_dur, alignment, fixed=self.hold)
        self.dur = self.T.duration
        self.nframes = int(round(self.dur * FPS))
        for e in self.els:
            e.resolve(self.T)
        self.chrome = []
        if self.chapter:
            self.chrome.append(Text(self.chapter.upper(), 96, 70, size=26, weight="Bold", color=YELLOW,
                                    anchor="lm", shadow=False, at=0.05, anim="left"))
        if self.src:
            self.chrome.append(Text("SOURCE: " + self.src.upper(), 96, H - 62, size=21, weight="SemiBold",
                                    color=(200, 206, 216), anchor="lm", bg=(0, 0, 0, 150), pad=(18, 10),
                                    radius=8, shadow=False, at=0.4, anim="fade"))
        for e in self.chrome:
            e.resolve(self.T)

    def shakes(self):
        return [e.t0 for e in self.els if getattr(e, "shake", False)]

    def sfx_events(self):
        ev = [(0.0, "whoosh")] if self.whip else []
        for e in self.els:
            if e.sfx:
                ev.append((e.t0, e.sfx))
            if isinstance(e, Shot):
                ev += e.sfx_times()
        return ev

    def frame(self, i):
        t = i / FPS
        img = background(self.glow).copy()
        for e in self.els:
            if e.visible(t):
                e.draw(img, t, self.T)
        # camera: slow push-in, shake on stamps, whip-in at the start
        z = 1 + self.push * ease_inout(t / self.dur)
        sx = sy = 0.0
        for st in self.shakes():
            if 0 <= t - st < 0.4:
                a = (1 - (t - st) / 0.4) * 16
                sx += a * math.sin((t - st) * 90)
                sy += a * math.cos((t - st) * 70)
        cw, ch = W / z, H / z
        x0 = clamp((W - cw) / 2 - sx / z, 0, W - cw)
        y0 = clamp((H - ch) / 2 - sy / z, 0, H - ch)
        out = img.resize((W, H), Image.BILINEAR, box=(x0, y0, x0 + cw, y0 + ch))
        if self.whip and t < 0.28:  # slide in from the right
            dx = int((1 - ease_out(t / 0.28)) * 260)
            slid = background(self.glow).copy()
            slid.alpha_composite(out.crop((0, 0, W - dx, H)), (dx, 0))
            out = slid
        # chrome is not affected by the camera
        for e in self.chrome:
            if e.visible(t):
                e.draw(out, t, self.T)
        arr = np.asarray(out.convert("RGB"), dtype=np.int16) + grain_frames()[i % 6]
        return np.clip(arr, 0, 255).astype(np.uint8)

    def render(self, path):
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
               "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast",
               "-crf", "18", "-pix_fmt", "yuv420p", path]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        for i in range(self.nframes):
            proc.stdin.write(self.frame(i).tobytes())
        proc.stdin.close()
        if proc.wait():
            raise RuntimeError(f"ffmpeg failed for scene {self.sid}")

    def still(self, path, t=None):
        t = self.dur - 0.05 if t is None else t
        Image.fromarray(self.frame(int(t * FPS))).save(path)
