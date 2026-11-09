"""Download the lead image (poster / infobox photo) for each mapped item from Wikipedia.
Usage: python3 -I tools/fetch_real_images.py   (run from holiday-ranking-lenses/)
Saves to sources/<lens-id>/<NN>.<ext> and writes sources/manifest.json."""
import json, os, re, ssl, sys, time, urllib.parse, urllib.request
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = {"User-Agent": "HolidayLensCards/1.0 (personal Snapchat lens project)"}
ca = os.environ.get("SSL_CERT_FILE") or ("/root/.ccr/ca-bundle.crt" if os.path.exists("/root/.ccr/ca-bundle.crt") else None)
CTX = ssl.create_default_context(cafile=ca) if ca else ssl.create_default_context()
API = "https://en.wikipedia.org/w/api.php?"

def get(url, raw=False):
    for attempt in range(6):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), context=CTX, timeout=30) as r:
                data = r.read()
                return data if raw else json.loads(data)
        except Exception as e:
            if attempt == 5: raise
            time.sleep(10 * (attempt + 1) if '429' in str(e) else 2 ** attempt)

def api(**p):
    p.update(format="json", formatversion=2)
    return get(API + urllib.parse.urlencode(p))

def infobox_file(title):
    d = api(action="parse", page=title, prop="wikitext", section=0, redirects=1)
    if "error" in d: return None
    wt = d["parse"]["wikitext"]
    for m in re.finditer(r"\|\s*(?:image|image_name|cover|poster)\s*=\s*([^\n|}]+)", wt):
        name = re.sub(r"^\[\[|^(File|Image):", "", m.group(1).strip(), flags=re.I).strip()
        if re.search(r"\.(jpe?g|png|webp|gif)$", name, re.I): return name
    m = re.search(r"\[\[(?:File|Image):([^|\]]+\.(?:jpe?g|png|webp))", wt, re.I)
    return m.group(1).strip() if m else None

def file_url(name):
    d = api(action="query", titles="File:" + name, prop="imageinfo", iiprop="url", iiurlwidth=800)
    pages = d["query"]["pages"]
    ii = pages[0].get("imageinfo") if pages else None
    return (ii[0].get("thumburl") or ii[0]["url"]) if ii else None

def lead_url(title):
    d = api(action="query", titles=title, prop="pageimages", piprop="thumbnail", pithumbsize=800, redirects=1)
    p = d["query"]["pages"][0]
    return p.get("thumbnail", {}).get("source")

cats = {c["id"]: c for c in json.load(open(os.path.join(ROOT, "tools", "categories.json")))}
mapping = json.load(open(os.path.join(ROOT, "tools", "real_images.json")))
only = sys.argv[1:]
manifest_path = os.path.join(ROOT, "sources", "manifest.json")
manifest = json.load(open(manifest_path)) if os.path.exists(manifest_path) else {}
for lens, items in mapping.items():
    if only and lens not in only: continue
    out = os.path.join(ROOT, "sources", lens); os.makedirs(out, exist_ok=True)
    names = [i[0] for i in cats[lens]["items"]]
    for name, article in items.items():
        idx = names.index(name) + 1
        key = f"{lens}/{idx:02d}"
        if key in manifest and os.path.exists(os.path.join(ROOT, "sources", manifest[key]["file"])): continue
        try:
            f = infobox_file(article)
            url = file_url(f) if f else None
            url = url or lead_url(article)
            if not url: print("MISS", lens, name, article); continue
            ext = os.path.splitext(urllib.parse.urlparse(url).path)[1].lower() or ".jpg"
            if ext not in (".jpg", ".jpeg", ".png", ".webp", ".gif"): ext = ".jpg"
            fn = f"{lens}/{idx:02d}{ext}"
            open(os.path.join(ROOT, "sources", fn), "wb").write(get(url, raw=True))
            manifest[key] = {"file": fn, "item": name, "article": article, "url": url}
            print("ok  ", lens, name)
        except Exception as e:
            print("ERR ", lens, name, article, e)
        time.sleep(1.5)
    json.dump(manifest, open(manifest_path, "w"), indent=1)
