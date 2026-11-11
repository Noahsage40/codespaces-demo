"""Find and download free-license video clips (b-roll) from Wikimedia Commons.

Usage: python3 -I pipeline/fetch_broll.py videos/2015-qbs "Kyler Murray" "Drew Lock" "football touchdown" ...
Saves to videos/<name>/broll/<query-slug>/NN.webm and appends attribution lines to broll/CREDITS.txt
(put CREDITS.txt in the video description: these clips are CC-licensed and need credit).
Goes slowly on purpose: Wikimedia rate-limits fast clients.
"""
import json, os, re, ssl, sys, time, urllib.parse, urllib.request

UA = {"User-Agent": "QBVideoBuilder/1.0 (https://github.com/noahsage40/codespaces-demo)"}
ca = "/root/.ccr/ca-bundle.crt"
CTX = ssl.create_default_context(cafile=ca) if os.path.exists(ca) else ssl.create_default_context()
API = "https://commons.wikimedia.org/w/api.php?"
PER_QUERY = int(os.environ.get("PER_QUERY", "4"))
MAX_BYTES = 80_000_000


def get(url, raw=False):
    for attempt in range(8):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), context=CTX, timeout=120) as r:
                data = r.read()
                return data if raw else json.loads(data)
        except Exception as e:
            wait = 45 * (attempt + 1) if "429" in str(e) or "Expecting value" in str(e) else 5 * (attempt + 1)
            print(f"   wait {wait}s ({e})", flush=True)
            time.sleep(wait)
    raise RuntimeError("gave up: " + url)


def api(**p):
    p.update(format="json", formatversion=2)
    return get(API + urllib.parse.urlencode(p))


def strip_html(s):
    return re.sub(r"<[^>]+>", "", s or "").strip()


def main():
    vdir = os.path.abspath(sys.argv[1])
    root = os.path.join(vdir, "broll")
    os.makedirs(root, exist_ok=True)
    credits = os.path.join(root, "CREDITS.txt")
    for q in sys.argv[2:]:
        slug = re.sub(r"[^a-z0-9]+", "-", q.lower()).strip("-")
        out = os.path.join(root, slug)
        os.makedirs(out, exist_ok=True)
        if len([f for f in os.listdir(out) if f.endswith(".webm")]) >= PER_QUERY:
            print(f"## {q}: already have clips"); continue
        res = api(action="query", list="search", srnamespace=6, srlimit=20, srsearch=q + " filetype:video")
        titles = [r["title"] for r in res["query"]["search"]]
        print(f"## {q}: {len(titles)} results", flush=True)
        n = 0
        for t in titles:
            if n >= PER_QUERY: break
            time.sleep(6)
            info = api(action="query", titles=t, prop="videoinfo", viprop="url|size|derivatives|extmetadata")
            vi = info["query"]["pages"][0].get("videoinfo", [{}])[0]
            if not vi: continue
            ders = [d for d in vi.get("derivatives", []) if d.get("height", 9999) <= 720 and "webm" in d.get("type", "")]
            ders.sort(key=lambda d: -d.get("height", 0))
            url = ders[0]["src"] if ders else vi.get("url")
            if not url or (not ders and vi.get("size", 0) > MAX_BYTES): continue
            meta = vi.get("extmetadata", {})
            lic = strip_html(meta.get("LicenseShortName", {}).get("value", ""))
            if not re.search(r"CC|Public domain|PD", lic, re.I): continue
            artist = strip_html(meta.get("Artist", {}).get("value", "unknown"))
            time.sleep(6)
            try:
                data = get(url, raw=True)
            except Exception as e:
                print("   skip", t, e); continue
            n += 1
            fn = os.path.join(out, f"{n:02d}.webm")
            open(fn, "wb").write(data)
            open(fn + ".txt", "w").write(t + "\n")
            with open(credits, "a") as f:
                f.write(f'"{t[5:]}" by {artist}, {lic}, via Wikimedia Commons\n')
            print(f"   ok {slug}/{n:02d}  {t}", flush=True)
        time.sleep(10)


if __name__ == "__main__":
    main()
