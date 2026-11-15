// Square real-photo cards for ranking lenses (exactly 10 per lens).
// Usage: node tools/render_photo_lens.js            (reads real-photo-lenses/lenses.json)
const fs = require('fs'), path = require('path');
const { chromium } = require('playwright');
const ROOT = path.resolve(__dirname, '..');
const lenses = JSON.parse(fs.readFileSync(path.join(ROOT, 'real-photo-lenses', 'lenses.json'), 'utf8'));
const MIME = { '.jpg': 'jpeg', '.jpeg': 'jpeg', '.png': 'png', '.webp': 'webp' };
const esc = s => s.replace(/&/g, '&amp;').replace(/</g, '&lt;');
const slug = s => s.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
const S = 600;

function card(name, file) {
  const src = `data:image/${MIME[path.extname(file).toLowerCase()] || 'jpeg'};base64,` + fs.readFileSync(file).toString('base64');
  const fsz = name.length <= 10 ? 66 : name.length <= 18 ? 54 : name.length <= 26 ? 44 : 38;
  return `<!doctype html><html><head><meta charset="utf-8"><style>
  *{margin:0;box-sizing:border-box}body{width:${S}px;height:${S}px;overflow:hidden;font-family:'Inter',sans-serif;background:#111}
  .bg{position:absolute;inset:-40px;background:url('${src}') center/cover;filter:blur(24px) brightness(.5)}
  .ph{position:absolute;inset:0;width:100%;height:100%;object-fit:contain}
  .ph.cover{object-fit:cover;object-position:center 35%}
  .shade{position:absolute;left:0;right:0;top:0;height:160px;background:linear-gradient(rgba(0,0,0,.6),transparent)}
  .t{position:absolute;left:0;right:0;top:0;padding:16px 18px;text-align:center;font-weight:900;font-size:${fsz}px;line-height:1;text-transform:uppercase;
     color:#fff;-webkit-text-stroke:3px #111;paint-order:stroke fill;text-shadow:0 3px 0 rgba(0,0,0,.4)}
  .f{position:absolute;inset:0;border:8px solid #fff}</style></head><body>
  <div class="bg"></div><img class="ph" id="p" src="${src}"><div class="shade"></div><div class="t">${esc(name)}</div><div class="f"></div>
  <script>const i=document.getElementById('p');const f=()=>{if(i.naturalWidth/i.naturalHeight>=0.8)i.classList.add('cover')};i.complete?f():i.onload=f;</script>
  </body></html>`;
}

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: S, height: S } });
  for (const lens of lenses) {
    if (lens.items.length !== 10) throw new Error(`${lens.id} needs exactly 10 items (has ${lens.items.length})`);
    const out = path.join(ROOT, 'real-photo-lenses', lens.id);
    fs.mkdirSync(out, { recursive: true });
    for (const f of fs.readdirSync(out)) if (f.endsWith('.jpg')) fs.unlinkSync(path.join(out, f));
    for (const [i, [name, src]] of lens.items.entries()) {
      await page.setContent(card(name, path.join(ROOT, 'sources', src)));
      await page.evaluate(async () => { await document.fonts.ready; await Promise.all([...document.images].map(i => i.decode().catch(() => {}))); });
      await page.screenshot({ path: path.join(out, `${String(i + 1).padStart(2, '0')}-${slug(name)}.jpg`), type: 'jpeg', quality: 88 });
    }
    console.log(lens.id, 'done');
  }
  await browser.close();
})();
