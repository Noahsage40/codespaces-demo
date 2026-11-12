"""Build a finished video from videos/<name>/script.json.

Steps: voiceover (per line) -> slides (node render_slides.js) -> slow-zoom clips per scene
-> fades -> burned-in captions -> optional background music -> final MP4.

Usage:
  python3 pipeline/build_video.py videos/2015-qbs                    # 16:9 long-form
  python3 pipeline/build_video.py videos/2015-qbs --vertical         # 9:16 Shorts/TikTok
  python3 pipeline/build_video.py videos/2015-qbs --voice elevenlabs # cloned voice

Voices:
  espeak      free placeholder voice (robotic), default
  elevenlabs  your cloned voice; needs ELEVENLABS_VOICE_ID (see clone_voice.py)
Music: drop a track at videos/<name>/music.mp3 and it is mixed quietly under the voice.
"""
import json, os, re, subprocess, sys, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
FPS = 30


def sh(cmd):
    subprocess.run(cmd, check=True)


def duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", path], capture_output=True, text=True, check=True)
    return float(out.stdout.strip())


# ---------------- voice ----------------
def tts_espeak(text, out_wav):
    sh(["espeak-ng", "-v", "mb-us2", "-s", "170", "-w", out_wav, text])


_KOKORO = None


def tts_kokoro(text, out_wav):
    """Free natural-sounding AI narrator (Kokoro). Model files live in $KOKORO_DIR."""
    global _KOKORO
    from kokoro_onnx import Kokoro
    import soundfile as sf
    if _KOKORO is None:
        d = os.environ.get("KOKORO_DIR", os.path.expanduser("~/kokoro"))
        _KOKORO = Kokoro(os.path.join(d, "kokoro-v1.0.onnx"), os.path.join(d, "voices-v1.0.bin"))
    audio, sr = _KOKORO.create(text, voice=os.environ.get("KOKORO_VOICE", "am_michael"), speed=1.08, lang="en-us")
    sf.write(out_wav, audio, sr)


def tts_elevenlabs(text, out_wav):
    voice = os.environ["ELEVENLABS_VOICE_ID"]
    body = json.dumps({"text": text, "model_id": "eleven_multilingual_v2",
                       "voice_settings": {"stability": 0.45, "similarity_boost": 0.85, "style": 0.3}}).encode()
    req = urllib.request.Request(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice}?output_format=mp3_44100_128",
        data=body, headers={"Content-Type": "application/json",
                            # the real key is injected by the environment's network proxy
                            "xi-api-key": os.environ.get("ELEVENLABS_API_KEY", "injected-by-proxy")})
    mp3 = out_wav[:-4] + ".mp3"
    with urllib.request.urlopen(req, timeout=120) as r, open(mp3, "wb") as f:
        f.write(r.read())
    sh(["ffmpeg", "-v", "error", "-y", "-i", mp3, out_wav])


# ---------------- captions ----------------
def ass_time(t):
    h, m = int(t // 3600), int(t % 3600 // 60)
    return f"{h}:{m:02d}:{t % 60:05.2f}"


def chunks(text, n):
    words = text.split()
    return [" ".join(words[i:i + n]) for i in range(0, len(words), n)]


def write_ass(cues, path, vertical):
    W, H = (1080, 1920) if vertical else (1920, 1080)
    size, margin = (88, 640) if vertical else (58, 70)
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Inter Black,{size},&H00FFFFFF,&H0042C5F5,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,{7 if vertical else 5},2,2,80,80,{margin},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = []
    for start, end, text in cues:
        if vertical:  # one event per word, current word in yellow
            ws = text.upper().split()
            total = sum(len(w) + 1 for w in ws)
            t = start
            for j, w in enumerate(ws):
                d = (end - start) * (len(w) + 1) / total
                txt = " ".join(("{\\c&H00E6FF&}" if k == j else "{\\c&HFFFFFF&}") + x for k, x in enumerate(ws))
                lines.append(f"Dialogue: 0,{ass_time(t)},{ass_time(t + d)},Cap,,0,0,0,,{txt}")
                t += d
        else:
            lines.append(f"Dialogue: 0,{ass_time(start)},{ass_time(end)},Cap,,0,0,0,,{text}")
    open(path, "w").write(head + "\n".join(lines) + "\n")


# ---------------- main ----------------
def main():
    args = sys.argv[1:]
    vdir = os.path.abspath(args[0])
    vertical = "--vertical" in args
    voice = args[args.index("--voice") + 1] if "--voice" in args else "espeak"
    tts = {"espeak": tts_espeak, "kokoro": tts_kokoro, "elevenlabs": tts_elevenlabs}[voice]
    W, H = (1080, 1920) if vertical else (1920, 1080)
    script = json.load(open(os.path.join(vdir, "script.json")))
    tag = ("vertical" if vertical else "long") + "-" + voice
    work = os.path.join(vdir, "build", tag)
    os.makedirs(work, exist_ok=True)

    print("rendering slides...")
    sh(["node", os.path.join(HERE, "render_slides.js"), vdir] + (["--vertical"] if vertical else []))
    slides = os.path.join(vdir, "slides-vertical" if vertical else "slides")

    GAP, TAIL = 0.28, 0.45
    cues, clips, t0 = [], [], 0.0
    words_per_cap = 3 if vertical else 7
    for si, sc in enumerate(script["scenes"]):
        # voice each line, then join with small pauses
        parts, t = [], 0.0
        for li, line in enumerate(sc["lines"]):
            wav = os.path.join(work, f"s{si:02d}_l{li:02d}.wav")
            cache = wav + ".txt"
            if not (os.path.exists(wav) and os.path.exists(cache) and open(cache).read() == line):
                tts(line, wav)
                open(cache, "w").write(line)
            d = duration(wav)
            # captions: split the line into chunks timed by character share
            cs = chunks(line, words_per_cap)
            total = sum(len(c) for c in cs)
            ct = t
            for c in cs:
                cd = d * len(c) / total
                cues.append((t0 + ct, t0 + ct + cd, c))
                ct += cd
            parts.append((wav, d))
            t += d + GAP
        scene_len = t - GAP + TAIL
        last = si == len(script["scenes"]) - 1
        # scene audio
        audio = os.path.join(work, f"scene{si:02d}.wav")
        inputs, filt = [], []
        for k, (wav, d) in enumerate(parts):
            inputs += ["-i", wav]
            tail = TAIL
            if last and k == len(parts) - 1:  # keep Shorts/TikToks over the monetization minimum
                tail = max(TAIL, script.get("min_seconds", 0) - (t0 + scene_len - TAIL))
            filt.append(f"[{k}]aresample=44100,aformat=channel_layouts=mono,apad=pad_dur={GAP if k < len(parts) - 1 else tail}[a{k}]")
        filt.append("".join(f"[a{k}]" for k in range(len(parts))) + f"concat=n={len(parts)}:v=0:a=1[out]")
        sh(["ffmpeg", "-v", "error", "-y"] + inputs + ["-filter_complex", ";".join(filt), "-map", "[out]", audio])
        scene_len = duration(audio)
        frames = int(round(scene_len * FPS))
        clip = os.path.join(work, f"scene{si:02d}.mp4")
        slide_png = os.path.join(slides, f"{si:02d}.png")
        # "nfl/c2.webm@8" = clip c2 starting 8 seconds in
        broll = []
        for b in sc.get("broll", []):
            name, _, off = b.partition("@")
            if os.path.exists(os.path.join(vdir, "broll", name)):
                broll.append((os.path.join(vdir, "broll", name), float(off) if off else None))
        hold = min(3.5, scene_len * 0.4) if broll else scene_len  # graphic shown at the end of footage scenes
        foot_len = scene_len - hold if broll else 0
        parts_v = []
        if broll:
            seg = foot_len / len(broll)
            for k, (b, off) in enumerate(broll):
                d_src = duration(b)
                start = off if off is not None else (min(1.0, max(d_src - seg, 0)) if d_src > seg else 0)
                start = min(start, max(d_src - 1.0, 0))
                pv = os.path.join(work, f"scene{si:02d}_f{k}.mp4")
                n = int(round(seg * FPS))
                sh(["ffmpeg", "-v", "error", "-y", "-stream_loop", "-1", "-ss", f"{start:.2f}", "-i", b, "-i", os.path.join(slides, f"{si:02d}_lower.png"),
                    "-filter_complex", f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,fps={FPS}[v];[v][1:v]overlay=0:0,format=yuv420p",
                    "-an", "-frames:v", str(n), "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", pv])
                parts_v.append(pv)
        # graphic: slow push-in on the slide
        n = int(round(hold * FPS))
        zoom = "min(1+0.00035*on,1.06)" if si % 2 == 0 else "max(1.06-0.00035*on,1)"
        pv = os.path.join(work, f"scene{si:02d}_slide.mp4")
        sh(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-framerate", str(FPS), "-i", slide_png,
            "-vf", f"scale={W * 2}:{H * 2},zoompan=z='{zoom}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={n}:s={W}x{H}:fps={FPS},format=yuv420p",
            "-frames:v", str(n), "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", pv])
        parts_v.append(pv)
        lst_s = os.path.join(work, f"scene{si:02d}_parts.txt")
        open(lst_s, "w").write("".join(f"file '{x}'\n" for x in parts_v))
        sh(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst_s, "-i", audio,
            "-vf", f"fade=t=in:st=0:d=0.25,fade=t=out:st={max(scene_len - 0.25, 0):.2f}:d=0.25,format=yuv420p",
            "-map", "0:v", "-map", "1:a", "-frames:v", str(frames), "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
            "-c:a", "aac", "-b:a", "192k", "-shortest", clip])
        clips.append(clip)
        t0 += scene_len
        print(f"scene {si + 1}/{len(script['scenes'])}  {scene_len:.1f}s")

    lst = os.path.join(work, "clips.txt")
    open(lst, "w").write("".join(f"file '{c}'\n" for c in clips))
    joined = os.path.join(work, "joined.mp4")
    sh(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", joined])

    ass = os.path.join(work, "captions.ass")
    write_ass(cues, ass, vertical)
    out_dir = os.path.join(vdir, "out")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, f"{os.path.basename(vdir)}-{tag}.mp4")
    music = os.path.join(vdir, "music.mp3")
    cmd = ["ffmpeg", "-v", "error", "-y", "-i", joined]
    if os.path.exists(music):
        cmd += ["-stream_loop", "-1", "-i", music, "-filter_complex",
                "[1:a]volume=0.12[m];[0:a][m]amix=inputs=2:duration=first:normalize=0[a]", "-map", "0:v", "-map", "[a]"]
    cmd += ["-vf", f"ass={ass}", "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-c:a", "aac", "-b:a", "192k",
            "-movflags", "+faststart", out]
    sh(cmd)
    print(f"done: {out}  ({duration(out) / 60:.1f} min)")


if __name__ == "__main__":
    main()
