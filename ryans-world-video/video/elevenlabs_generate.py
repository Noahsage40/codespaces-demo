"""Generate the voiceover with your cloned ElevenLabs voice, one file per scene, with timings.

    export ELEVENLABS_API_KEY=...        # from elevenlabs.io → Profile → API keys
    export ELEVENLABS_VOICE_ID=...       # your cloned voice's ID (Voices → your voice → ID)
    python elevenlabs_generate.py        # all scenes
    python elevenlabs_generate.py --only 10,11   # redo some scenes

Writes audio/elevenlabs/<scene>.mp3 and <scene>.json (character timings). Then run:
    python build.py render

Each request passes the previous and next scene's text so the delivery flows across scene breaks.
Not tested from this environment (no API key here); check one scene first with --only 01.
"""
import argparse
import base64
import json
import os
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from scenes import SCENES  # noqa: E402

OUT = os.path.join(os.path.dirname(HERE), "audio", "elevenlabs")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only")
    ap.add_argument("--model", default="eleven_multilingual_v2")
    ap.add_argument("--stability", type=float, default=0.45)
    ap.add_argument("--similarity", type=float, default=0.85)
    ap.add_argument("--style", type=float, default=0.15)
    args = ap.parse_args()
    key, voice = os.environ.get("ELEVENLABS_API_KEY"), os.environ.get("ELEVENLABS_VOICE_ID")
    if not key or not voice:
        sys.exit("set ELEVENLABS_API_KEY and ELEVENLABS_VOICE_ID first")
    os.makedirs(OUT, exist_ok=True)
    spoken = [s for s in SCENES if s.text]
    want = set(args.only.split(",")) if args.only else None
    for i, s in enumerate(spoken):
        if want and not any(s.sid.startswith(k.zfill(2)) for k in want):
            continue
        body = {
            "text": s.text,
            "model_id": args.model,
            "previous_text": spoken[i - 1].text if i else None,
            "next_text": spoken[i + 1].text if i + 1 < len(spoken) else None,
            "voice_settings": {"stability": args.stability, "similarity_boost": args.similarity,
                               "style": args.style, "use_speaker_boost": True},
        }
        req = urllib.request.Request(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice}/with-timestamps?output_format=mp3_44100_128",
            data=json.dumps(body).encode(), headers={"xi-api-key": key, "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=180) as r:
            data = json.load(r)
        open(os.path.join(OUT, f"{s.sid}.mp3"), "wb").write(base64.b64decode(data["audio_base64"]))
        json.dump(data["alignment"], open(os.path.join(OUT, f"{s.sid}.json"), "w"))
        print("voiced", s.sid)


if __name__ == "__main__":
    main()
