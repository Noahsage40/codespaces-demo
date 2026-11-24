"""Build the video.

  python build.py narration          export one text file per scene for the voiceover
  python build.py scratch            make a robotic placeholder voice (espeak-ng) for timing
  python build.py stills             one PNG per scene (end state) for a quick visual check
  python build.py render             render every scene and assemble out/ryans_world.mp4
  python build.py render --only 10,11  re-render just some scenes, then reassemble

Voice priority per scene: audio/elevenlabs/<scene>.mp3|wav, then audio/scratch/<scene>.wav, then silence.
If audio/elevenlabs/<scene>.json exists (ElevenLabs "with timestamps" alignment), cues use exact word timings.
"""
import argparse
import json
import os
import subprocess
import sys
import wave
from multiprocessing import Pool

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from engine import FPS, LEAD  # noqa: E402
from scenes import SCENES  # noqa: E402

ROOT = os.path.dirname(HERE)
AUDIO = os.path.join(ROOT, "audio")
EL_DIR, SCRATCH_DIR = os.path.join(AUDIO, "elevenlabs"), os.path.join(AUDIO, "scratch")
NARR_DIR = os.path.join(ROOT, "narration")
BUILD, OUT = os.path.join(ROOT, "build"), os.path.join(ROOT, "out")
SR = 48000
WPS = 2.6  # words per second when no audio exists


def by_id():
    return {s.sid: s for s in SCENES}


# --------------------------------------------------------------------------- audio helpers
def decode(path):
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", path, "-f", "s16le", "-ac", "1", "-ar", str(SR), "-"],
                         check=True, capture_output=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768


def voice_for(scene):
    """Returns (samples or None, alignment or None, label)."""
    for ext in ("mp3", "wav"):
        p = os.path.join(EL_DIR, f"{scene.sid}.{ext}")
        if os.path.exists(p):
            al = None
            jp = os.path.join(EL_DIR, f"{scene.sid}.json")
            if os.path.exists(jp):
                a = json.load(open(jp))
                a = a.get("alignment", a)
                al = {"chars": a["characters"], "starts": a["character_start_times_seconds"]}
            return decode(p), al, "elevenlabs"
    p = os.path.join(SCRATCH_DIR, f"{scene.sid}.wav")
    if os.path.exists(p):
        return decode(p), None, "scratch"
    return None, None, "silent"


def setup(scene):
    if scene.hold:
        scene.setup(0)
        return None
    samples, al, _ = voice_for(scene)
    dur = len(samples) / SR if samples is not None else len(scene.text.split()) / WPS
    scene.setup(dur, al)
    return samples


def synth(kind):
    t = np.arange(int(SR * {"pop": 0.12, "hit": 0.6, "whoosh": 0.45, "swipe": 0.3}[kind])) / SR
    rng = np.random.default_rng(len(kind))
    if kind == "pop":
        f = 900 * np.exp(-t * 18) + 380
        y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 32) * 0.5
    elif kind == "hit":
        f = 140 * np.exp(-t * 6) + 45
        body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7)
        noise = rng.normal(0, 1, len(t)) * np.exp(-t * 40) * 0.35
        y = (body + noise) * 0.75
    elif kind == "whoosh":
        n = rng.normal(0, 1, len(t))
        k = 60
        n = np.convolve(n, np.ones(k) / k, mode="same") * 4
        env = np.sin(np.pi * np.clip(t / t[-1], 0, 1)) ** 2
        y = n * env * 0.35
    else:  # swipe: short airy marker sound
        n = rng.normal(0, 1, len(t))
        n = n - np.convolve(n, np.ones(8) / 8, mode="same")
        env = np.sin(np.pi * np.clip(t / t[-1], 0, 1)) ** 3
        y = n * env * 0.12
    return y.astype(np.float32)


def write_wav(path, y):
    y = np.clip(y, -1, 1)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((y * 32767).astype(np.int16).tobytes())


# --------------------------------------------------------------------------- commands
def cmd_narration(_):
    os.makedirs(NARR_DIR, exist_ok=True)
    full = []
    for s in SCENES:
        if s.text:
            open(os.path.join(NARR_DIR, f"{s.sid}.txt"), "w").write(s.text + "\n")
            full.append(s.text)
    open(os.path.join(NARR_DIR, "_full_script.txt"), "w").write("\n\n".join(full) + "\n")
    words = sum(len(t.split()) for t in full)
    print(f"wrote {len(full)} scene files to narration/ ({words} words, ~{words / 150:.1f} min at 150 wpm)")


def cmd_scratch(_):
    os.makedirs(SCRATCH_DIR, exist_ok=True)
    for s in SCENES:
        if s.text:
            subprocess.run(["espeak-ng", "-v", "en-us", "-s", "165", "-w", os.path.join(SCRATCH_DIR, f"{s.sid}.wav"),
                            s.text], check=True)
    print(f"placeholder voice written to {SCRATCH_DIR}")


def cmd_stills(args):
    out = os.path.join(BUILD, "stills")
    os.makedirs(out, exist_ok=True)
    for s in select(args):
        setup(s)
        s.still(os.path.join(out, f"{s.sid}.png"), None if args.t is None else args.t)
        print("still", s.sid, f"{s.dur:.1f}s")


def render_one(sid):
    s = by_id()[sid]
    setup(s)
    os.makedirs(os.path.join(BUILD, "segments"), exist_ok=True)
    s.render(os.path.join(BUILD, "segments", f"{sid}.mp4"))
    return sid, s.dur


def select(args):
    if not args.only:
        return SCENES
    keys = args.only.split(",")
    return [s for s in SCENES if any(s.sid.startswith(k.zfill(2)) or s.sid == k for k in keys)]


def cmd_render(args):
    todo = [s.sid for s in select(args)]
    with Pool(args.jobs) as pool:
        for sid, dur in pool.imap_unordered(render_one, todo):
            print(f"rendered {sid} ({dur:.1f}s)", flush=True)
    assemble(args)


def assemble(args):
    os.makedirs(OUT, exist_ok=True)
    seg_dir = os.path.join(BUILD, "segments")
    missing = [s.sid for s in SCENES if not os.path.exists(os.path.join(seg_dir, f"{s.sid}.mp4"))]
    if missing:
        sys.exit(f"missing segments, render them first: {missing}")
    # audio track: voice + sound effects, with sample counts matching the video frames exactly
    tracks, sources = [], {}
    sfx_cache = {}
    for s in SCENES:
        voice = setup(s)
        n = int(round(s.nframes / FPS * SR))
        track = np.zeros(n, np.float32)
        if voice is not None:
            st = int(LEAD * SR)
            seg = voice[: max(0, n - st)]
            track[st:st + len(seg)] += seg
        sources[s.sid] = voice_for(s)[2] if not s.hold else "-"
        if not args.no_sfx:
            for t, kind in s.sfx_events():
                fx = sfx_cache.setdefault(kind, synth(kind))
                i = int(t * SR)
                if 0 <= i < n:
                    part = fx[: n - i]
                    track[i:i + len(part)] += part * (0.55 if kind != "hit" else 0.7)
        tracks.append(track)
    mix = np.concatenate(tracks)
    peak = np.max(np.abs(mix)) or 1
    mix = mix / max(1.0, peak / 0.95)
    wav = os.path.join(BUILD, "mix.wav")
    write_wav(wav, mix)
    lst = os.path.join(BUILD, "segments.txt")
    with open(lst, "w") as f:
        for s in SCENES:
            f.write(f"file '{os.path.join(seg_dir, s.sid + '.mp4')}'\n")
    final = os.path.join(OUT, "ryans_world.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-i", wav,
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11",
                    "-movflags", "+faststart", "-shortest", final], check=True)
    total = len(mix) / SR
    voices = sorted(set(v for v in sources.values() if v != "-"))
    print(f"\n{final}  {int(total // 60)}:{int(total % 60):02d}  voice: {', '.join(voices)}")
    write_chapters()


def write_chapters():
    """YouTube chapter timestamps for the description, from the real scene timings."""
    t, lines, seen = 0.0, [], set()
    for s in SCENES:
        setup(s)
        name = s.chapter.split("·")[1].strip() if s.chapter and "·" in s.chapter else None
        if s.sid.startswith("01"):
            name = "The $100 million claim"
        if name and name not in seen:
            seen.add(name)
            lines.append(f"{int(t // 60)}:{int(t % 60):02d} {name}")
        t += s.nframes / FPS
    path = os.path.join(OUT, "chapters.txt")
    open(path, "w").write("\n".join(lines) + "\n")
    print("chapters:\n" + "\n".join(lines))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["narration", "scratch", "stills", "render", "assemble"])
    ap.add_argument("--only", help="comma-separated scene numbers, e.g. 10,11")
    ap.add_argument("--jobs", type=int, default=os.cpu_count())
    ap.add_argument("--no-sfx", action="store_true")
    ap.add_argument("--t", type=float, help="time for stills (default: end of scene)")
    args = ap.parse_args()
    {"narration": cmd_narration, "scratch": cmd_scratch, "stills": cmd_stills, "render": cmd_render,
     "assemble": assemble}[args.cmd](args)


if __name__ == "__main__":
    main()
