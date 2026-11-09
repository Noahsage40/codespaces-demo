// Renders every card (512x512 JPG) + the transparent 1-10 number strip.
// Usage: node tools/render_cards.js   (run from holiday-ranking-lenses/)
const fs = require('fs'), path = require('path');
const { chromium } = require('playwright');
const ROOT = path.resolve(__dirname, '..');
const cats = JSON.parse(fs.readFileSync(path.join(__dirname, 'categories.json'), 'utf8'));

const THEMES = {
  'xmas-red':   { bg: 'radial-gradient(circle at 50% 35%, #e2263f 0%, #a50f26 55%, #5e0716 100%)', band: '#0f5a2c', accent: '#ffd54a', pattern: 'snow', tag: '🎄' },
  'xmas-green': { bg: 'radial-gradient(circle at 50% 35%, #2a9653 0%, #146b35 55%, #07361a 100%)', band: '#b5132c', accent: '#ffd54a', pattern: 'snow', tag: '🎄' },
  'tg-orange':  { bg: 'radial-gradient(circle at 50% 35%, #ffa23a 0%, #e0661a 55%, #8a3208 100%)', band: '#5a2e12', accent: '#ffe08a', pattern: 'leaf', tag: '🦃' },
  'tg-brown':   { bg: 'radial-gradient(circle at 50% 35%, #b4652a 0%, #7d3f17 55%, #3e1e09 100%)', band: '#d9661c', accent: '#ffe08a', pattern: 'leaf', tag: '🦃' },
};
const esc = s => s.replace(/&/g,'&amp;').replace(/</g,'&lt;');
const slug = s => s.toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'');

function cardHTML(cat, [name, emoji]) {
  const t = THEMES[cat.theme];
  const len = name.length;
  const fs_ = len <= 10 ? 62 : len <= 16 ? 52 : len <= 24 ? 42 : len <= 34 ? 35 : 30;
  const deco = t.pattern === 'snow'
    ? `radial-gradient(circle, rgba(255,255,255,.55) 2.2px, transparent 3px) 0 0/46px 46px, radial-gradient(circle, rgba(255,255,255,.35) 1.6px, transparent 2.4px) 23px 23px/46px 46px`
    : `radial-gradient(circle, rgba(255,225,150,.22) 3px, transparent 4px) 0 0/54px 54px`;
  return `<!doctype html><html><head><meta charset="utf-8"><style>
  *{margin:0;box-sizing:border-box}
  body{width:512px;height:512px;overflow:hidden;font-family:'Inter','Inter Display',sans-serif}
  .card{position:relative;width:512px;height:512px;background:${deco},${t.bg};border:10px solid #fff;display:flex;flex-direction:column}
  .title{flex:0 0 auto;min-height:150px;display:flex;align-items:center;justify-content:center;text-align:center;padding:18px 22px 6px;
    font-weight:900;font-size:${fs_}px;line-height:1.02;text-transform:uppercase;color:#fff;letter-spacing:-.5px;
    -webkit-text-stroke:2px #1a1a1a;paint-order:stroke fill;text-shadow:0 4px 0 rgba(0,0,0,.35)}
  .art{flex:1;display:flex;align-items:center;justify-content:center;font-family:'Noto Color Emoji';
    font-size:${[...emoji].length>3?120:170}px;line-height:1;filter:drop-shadow(0 10px 12px rgba(0,0,0,.35));padding-bottom:42px}
  .tag{position:absolute;left:0;right:0;bottom:0;height:44px;background:${t.band};color:${t.accent};display:flex;align-items:center;justify-content:center;
    font-weight:800;font-size:19px;letter-spacing:2px;text-transform:uppercase}
  .tag i{font-style:normal;font-family:'Noto Color Emoji';margin-right:8px;letter-spacing:0}
  </style></head><body><div class="card"><div class="title">${esc(name)}</div><div class="art">${emoji}</div>
  <div class="tag"><i>${t.tag}</i>${esc(cat.title)}</div></div></body></html>`;
}

const MANIFEST_PATH = path.join(ROOT, 'sources', 'manifest.json');
const manifest = fs.existsSync(MANIFEST_PATH) ? JSON.parse(fs.readFileSync(MANIFEST_PATH, 'utf8')) : {};
const MIME = { '.jpg': 'jpeg', '.jpeg': 'jpeg', '.png': 'png', '.webp': 'webp', '.gif': 'gif' };

// Real-photo card: photo fills the card (posters sit on a blurred copy of themselves), bold title on top.
function photoHTML(cat, [name], file) {
  const ext = path.extname(file).toLowerCase();
  const src = `data:image/${MIME[ext] || 'jpeg'};base64,` + fs.readFileSync(file).toString('base64');
  const len = name.length;
  const fs_ = len <= 10 ? 58 : len <= 16 ? 48 : len <= 24 ? 40 : len <= 34 ? 33 : 28;
  return `<!doctype html><html><head><meta charset="utf-8"><style>
  *{margin:0;box-sizing:border-box}
  body{width:512px;height:512px;overflow:hidden;font-family:'Inter',sans-serif;background:#111}
  .card{position:relative;width:512px;height:512px;overflow:hidden;background:#222}
  .blur{position:absolute;inset:-30px;background:url('${src}') center/cover;filter:blur(22px) brightness(.55)}
  .ph{position:absolute;inset:0;width:100%;height:100%;object-fit:contain;object-position:center 70%}
  .ph.cover{object-fit:cover;object-position:center 40%}
  .shade{position:absolute;left:0;right:0;top:0;height:170px;background:linear-gradient(rgba(0,0,0,.55),rgba(0,0,0,0))}
  .title{position:absolute;left:0;right:0;top:0;padding:16px 18px;text-align:center;font-weight:900;font-size:${fs_}px;line-height:1.0;
    text-transform:uppercase;color:#fff;letter-spacing:-.5px;-webkit-text-stroke:3px #111;paint-order:stroke fill;text-shadow:0 3px 0 rgba(0,0,0,.4)}
  .frame{position:absolute;inset:0;border:8px solid #fff}
  </style></head><body><div class="card"><div class="blur"></div>
  <img class="ph" id="ph" src="${src}"><div class="shade"></div><div class="title">${esc(name)}</div><div class="frame"></div></div>
  <script>const i=document.getElementById('ph');const f=()=>{if(i.naturalWidth/i.naturalHeight>=0.78)i.classList.add('cover')};i.complete?f():i.onload=f;</script>
  </body></html>`;
}

function stripHTML() {
  let boxes = '';
  for (let i = 1; i <= 10; i++) boxes += `<div class="b">${i}</div>`;
  return `<!doctype html><html><head><meta charset="utf-8"><style>
  *{margin:0;box-sizing:border-box} html,body{background:transparent}
  body{width:160px;height:1600px;display:flex;flex-direction:column;font-family:'Inter'}
  .b{height:160px;margin:8px;flex:0 0 144px;border-radius:14px;background:rgba(40,36,34,.82);color:#fff;font-weight:900;font-size:96px;
     display:flex;align-items:center;justify-content:center;letter-spacing:-4px}
  </style></head><body>${boxes}</body></html>`;
}

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 512, height: 512 } });
  for (const cat of cats) {
    const dir = path.join(ROOT, 'lenses', cat.id);
    fs.mkdirSync(dir, { recursive: true });
    for (const f of fs.readdirSync(dir)) if (f.endsWith('.jpg')) fs.unlinkSync(path.join(dir, f));
    for (const [i, item] of cat.items.entries()) {
      const m = manifest[`${cat.id}/${String(i + 1).padStart(2, '0')}`];
      const photo = m && fs.existsSync(path.join(ROOT, 'sources', m.file));
      await page.setContent(photo ? photoHTML(cat, item, path.join(ROOT, 'sources', m.file)) : cardHTML(cat, item));
      await page.evaluate(async () => { await document.fonts.ready; await Promise.all([...document.images].map(i => i.decode().catch(() => {}))); });
      const file = path.join(dir, `${String(i + 1).padStart(2, '0')}-${slug(item[0])}.jpg`);
      await page.screenshot({ path: file, type: 'jpeg', quality: 86 });
    }
    console.log(cat.id, cat.items.length);
  }
  const sp = await browser.newPage({ viewport: { width: 160, height: 1600 } });
  await sp.setContent(stripHTML());
  await sp.evaluate(() => document.fonts.ready);
  await sp.screenshot({ path: path.join(ROOT, 'lens-studio', 'number-strip.png'), omitBackground: true });
  await browser.close();
})();
