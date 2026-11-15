"""Download candidate photos from Openverse (openly licensed, mostly Flickr) for each item.
Usage: python3 -I tools/fetch_openverse.py OUTDIR "Item name=search query" ...
Saves OUTDIR/<slug>/c1.jpg..c4.jpg and OUTDIR/<slug>/credits.json"""
import json, os, re, ssl, sys, time, urllib.parse, urllib.request
out = sys.argv[1]
UA = {"User-Agent": "HolidayLensCards/1.0 (https://github.com/noahsage40/codespaces-demo)"}
ca = "/root/.ccr/ca-bundle.crt"
CTX = ssl.create_default_context(cafile=ca) if os.path.exists(ca) else ssl.create_default_context()
def get(url, raw=False):
    for a in range(5):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), context=CTX, timeout=60) as r:
                b = r.read(); return b if raw else json.loads(b)
        except Exception as e:
            print("  retry", str(e)[:60], flush=True); time.sleep(10 * (a + 1))
    return None
for arg in sys.argv[2:]:
    name, _, q = arg.partition("=")
    q = q or name
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    d = os.path.join(out, slug); os.makedirs(d, exist_ok=True)
    res = get("https://api.openverse.org/v1/images/?" + urllib.parse.urlencode(
        dict(q=q, license_type="commercial", page_size=12, mature="false", source="flickr")))
    credits, n = [], 0
    for r in (res or {}).get("results", []):
        if n >= 4: break
        if (r.get("width") or 0) < 600 or (r.get("height") or 0) < 450: continue
        img = get(r["url"], raw=True)
        if not img or img[:3] != b"\xff\xd8\xff": continue
        n += 1
        open(os.path.join(d, f"c{n}.jpg"), "wb").write(img)
        credits.append({"file": f"c{n}.jpg", "title": r["title"], "creator": r.get("creator"),
                        "license": f"CC {r['license'].upper()} {r['license_version']}", "source": r.get("foreign_landing_url")})
        time.sleep(1)
    json.dump(credits, open(os.path.join(d, "credits.json"), "w"), indent=1)
    print(name, n, flush=True)
