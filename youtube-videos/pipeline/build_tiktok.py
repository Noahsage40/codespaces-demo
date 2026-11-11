"""Split-screen TikTok / Shorts builder.

Top half: you talking (your filmed clip).  Bottom half: "film room" graphics that change with each beat.
Middle: big word-by-word captions with the current word in yellow.  First seconds: a hook bubble.

Usage:
  python3 pipeline/build_tiktok.py videos/home-alone-tiktok --clip path/to/your_clip.mp4
  python3 pipeline/build_tiktok.py videos/home-alone-tiktok --preview STANDIN.mp4 [--crop w:h:x:y]

With --clip: your clip is transcribed (word timings), long pauses are cut out, and the graphics switch
when you start each beat's first words.  With --preview: a stand-in video plus the placeholder voice.
"""
import json, os, re, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_video import sh, duration, tts_espeak, ass_time  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
FPS = 30
YELLOW = r"{\c&H00E6FF&}"  # ASS colours are BGR
WHITE = r"{\c&HFFFFFF&}"


def norm(w):
    return re.sub(r"[^a-z0-9]", "", w.lower())


def caption_events(words, per=3):
    """words: list of (start, end, text). Emits one event per word; the chunk is shown with that word yellow."""
    ev = []
    for i in range(0, len(words), per):
        chunk = words[i:i + per]
        for j, (s, e, _) in enumerate(chunk):
            end = chunk[j + 1][0] if j + 1 < len(chunk) else e
            txt = " ".join((YELLOW if k == j else WHITE) + w.upper() for k, (_, _, w) in enumerate(chunk))
            ev.append((s, max(end, s + 0.05), txt))
    return ev


def write_ass(events, path):
    head = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Inter Black,78,&H00FFFFFF,&H00FFFFFF,&H00000000,&H96000000,-1,0,0,0,100,100,0,0,1,7,3,5,60,60,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    body = "".join(f"Dialogue: 0,{ass_time(s)},{ass_time(e)},Cap,,0,0,0,,{{\\pos(540,960)}}{t}\n" for s, e, t in events)
    open(path, "w").write(head + body)


def words_from_tts(script, work):
    """Preview mode: voice every line with the placeholder voice; spread word timings across each line."""
    words, beat_starts, parts, t = [], [], [], 0.0
    for bi, beat in enumerate(script["beats"]):
        beat_starts.append(t)
        for li, line in enumerate(beat["lines"]):
            wav = os.path.join(work, f"b{bi:02d}_l{li:02d}.wav")
            tts_espeak(line, wav)
            d = duration(wav)
            ws = line.split()
            total = sum(len(w) + 1 for w in ws)
            ct = t
            for w in ws:
                wd = d * (len(w) + 1) / total
                words.append((ct, ct + wd, w))
                ct += wd
            parts.append(wav)
            t += d + 0.15
    audio = os.path.join(work, "voice.wav")
    ins, flt = [], []
    for k, p in enumerate(parts):
        ins += ["-i", p]
        flt.append(f"[{k}]aresample=44100,aformat=channel_layouts=mono,apad=pad_dur=0.15[a{k}]")
    flt.append("".join(f"[a{k}]" for k in range(len(parts))) + f"concat=n={len(parts)}:v=0:a=1[o]")
    sh(["ffmpeg", "-v", "error", "-y"] + ins + ["-filter_complex", ";".join(flt), "-map", "[o]", audio])
    return words, beat_starts, audio, duration(audio)


def words_from_clip(script, clip, work):
    """Real mode: transcribe the clip, cut pauses longer than 0.5s, find where each beat starts."""
    from faster_whisper import WhisperModel
    model = WhisperModel("small.en", device="cpu", compute_type="int8")
    segs, _ = model.transcribe(clip, word_timestamps=True, vad_filter=True)
    raw = [(w.start, w.end, w.word.strip()) for s in segs for w in s.words if w.word.strip()]
    # keep-ranges: merge words separated by < 0.5s
    keep = []
    for s, e, _ in raw:
        if keep and s - keep[-1][1] < 0.5:
            keep[-1][1] = e
        else:
            keep.append([max(s - 0.08, 0), e + 0.12])
    # remap word times onto the cut timeline
    words, offset_map, acc = [], [], 0.0
    for a, b in keep:
        offset_map.append((a, b, acc))
        acc += b - a
    def remap(t):
        for a, b, o in offset_map:
            if a <= t <= b:
                return o + t - a
        return None
    for s, e, w in raw:
        rs, re_ = remap(s), remap(e)
        if rs is not None and re_ is not None:
            words.append((rs, re_, w))
    # beat starts: first occurrence (in order) of each beat's first 3 words
    seq = [norm(w) for _, _, w in words]
    beat_starts, pos = [], 0
    for beat in script["beats"]:
        key = [norm(w) for w in beat["lines"][0].split()[:3]]
        found = None
        for i in range(pos, len(seq) - len(key) + 1):
            if sum(a == b for a, b in zip(seq[i:i + len(key)], key)) >= 2:
                found = i
                break
        if found is None:
            beat_starts.append(beat_starts[-1] + 3 if beat_starts else 0.0)
        else:
            beat_starts.append(words[found][0])
            pos = found + 1
    beat_starts[0] = 0.0
    # cut the clip
    sel = "+".join(f"between(t,{a:.3f},{b:.3f})" for a, b in keep)
    cut = os.path.join(work, "clip_cut.mp4")
    sh(["ffmpeg", "-v", "error", "-y", "-i", clip, "-vf", f"select='{sel}',setpts=N/FRAME_RATE/TB",
        "-af", f"aselect='{sel}',asetpts=N/SR/TB", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", cut])
    return words, beat_starts, cut, duration(cut)


def main():
    a = sys.argv[1:]
    vdir = os.path.abspath(a[0])
    script = json.load(open(os.path.join(vdir, "script.json")))
    preview = "--preview" in a
    src = a[a.index("--preview") + 1] if preview else a[a.index("--clip") + 1]
    crop = a[a.index("--crop") + 1] if "--crop" in a else None
    work = os.path.join(vdir, "build", "preview" if preview else "final")
    os.makedirs(work, exist_ok=True)

    sh(["node", os.path.join(HERE, "render_boards.js"), vdir])
    boards = os.path.join(vdir, "boards")

    if preview:
        words, starts, audio, T = words_from_tts(script, work)
        standin = os.path.join(work, "standin.mp4")  # trim the stand-in so its ending never shows
        sh(["ffmpeg", "-v", "error", "-y", "-ss", "0.5", "-t", "9", "-i", src, "-an", "-c:v", "libx264", "-preset", "veryfast", standin])
        face_in = ["-stream_loop", "-1", "-i", standin]
        audio_in = ["-i", audio]
    else:
        words, starts, cut, T = words_from_clip(script, src, work)
        face_in = ["-i", cut]
        audio_in = ["-i", cut]

    # bottom half: one slow-zoom clip per beat
    clips = []
    for i, st in enumerate(starts):
        end = starts[i + 1] if i + 1 < len(starts) else T
        d = max(end - st, 0.5)
        n = int(round(d * FPS))
        c = os.path.join(work, f"board{i:02d}.mp4")
        sh(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-framerate", str(FPS), "-i", os.path.join(boards, f"b{i:02d}.png"),
            "-vf", f"scale=2160:1920,zoompan=z='1.04+0.03*sin(on/{FPS}*0.6)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={n}:s=1080x960:fps={FPS},format=yuv420p",
            "-frames:v", str(n), "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", c])
        clips.append(c)
    lst = os.path.join(work, "boards.txt")
    open(lst, "w").write("".join(f"file '{c}'\n" for c in clips))
    bottom = os.path.join(work, "bottom.mp4")
    sh(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", bottom])

    ass = os.path.join(work, "captions.ass")
    write_ass(caption_events(words), ass)
    out_dir = os.path.join(vdir, "out")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, os.path.basename(vdir) + ("-preview" if preview else "") + ".mp4")
    top = (f"crop={crop}," if crop else "") + "scale=1080:960:force_original_aspect_ratio=increase,crop=1080:960,setsar=1,fps=30"
    hook = os.path.join(boards, "hook.png")
    fc = (f"[0:v]{top}[top];[1:v]setsar=1[bot];[top][bot]vstack=inputs=2[v0];"
          f"[v0][3:v]overlay=x=(W-w)/2:y=110:enable='lt(t,3.2)'[v1];[v1]ass={ass}[v]")
    sh(["ffmpeg", "-v", "error", "-y"] + face_in + ["-i", bottom] + audio_in + ["-i", hook,
        "-filter_complex", fc, "-map", "[v]", "-map", "2:a", "-t", f"{T:.2f}",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out])
    print(f"done: {out}  ({T:.1f}s)")


if __name__ == "__main__":
    main()
