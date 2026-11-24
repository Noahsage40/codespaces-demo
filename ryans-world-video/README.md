# Ryan's World investigation video

The whole video is generated from code: every graphic, screenshot zoom, highlight, stamp, sound effect and the edit itself. The voice is the only thing you add.

| File | What it is |
|---|---|
| `script.md` | The script with visual notes |
| `sources.md` | Every claim with its source and a reliability rating |
| `numbers.md` | All the calculations |
| `upload.md` | Title options, YouTube description, upload checklist |
| `narration/` | The voiceover text, one file per scene (`_full_script.txt` has it all) |
| `video/scenes.py` | Every scene: narration plus the visuals cued to specific words |
| `video/engine.py` | The motion-graphics engine |
| `video/build.py` | Renders and assembles the video |
| `video/elevenlabs_generate.py` | Voices every scene with your cloned voice |
| `assets/screens/` | Screenshots used in the video |

## Make the final video with your voice

You need Python 3 with `numpy` and `Pillow`, plus `ffmpeg`.

```bash
cd video
export ELEVENLABS_API_KEY=your_key
export ELEVENLABS_VOICE_ID=your_cloned_voice_id
python elevenlabs_generate.py --only 01     # try one scene first and listen to it
python elevenlabs_generate.py               # then all scenes
python build.py render                      # about 10 minutes on 4 cores
```

The output is `out/ryans_world.mp4`, and `out/chapters.txt` holds the YouTube chapter timestamps.

Because ElevenLabs returns timings for every character, each pop-up, highlight and stamp lands on the exact word it's tied to. Scene lengths stretch or shrink to fit your delivery automatically.

**If you'd rather use the ElevenLabs website:** paste each file from `narration/` into it, download each result as `audio/elevenlabs/<scene name>.mp3` (for example `10_forbes.mp3`), then run `python build.py render`. Without the timing files, cues are placed by the position of the words in the text, which is close but less exact.

## Changing things

- **Wording:** edit the narration in `video/scenes.py`, re-voice just that scene (`python elevenlabs_generate.py --only 10`), then `python build.py render --only 10`.
- **Quick visual check:** `python build.py stills` writes one image per scene to `build/stills/`.
- **No sound effects:** `python build.py render --no-sfx`.
- **Placeholder voice** (robotic, for checking timing only): `python build.py scratch`.
