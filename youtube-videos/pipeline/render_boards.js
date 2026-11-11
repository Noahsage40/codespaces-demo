// Renders the bottom-half "playbook" graphics for a TikTok (1080x960 each) + the hook bubble.
// Usage: node pipeline/render_boards.js videos/home-alone-tiktok
const fs = require('fs'), path = require('path');
const { chromium } = require('playwright');
const dir = path.resolve(process.argv[2]);
const script = JSON.parse(fs.readFileSync(path.join(dir, 'script.json'), 'utf8'));
const out = path.join(dir, 'boards');
fs.mkdirSync(out, { recursive: true });
const esc = s => String(s ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;');

// X's and O's doodles scattered on the chalkboard
function chalk(seed) {
  let r = seed * 9301 + 49297, rnd = () => ((r = (r * 9301 + 49297) % 233280) / 233280);
  let s = '';
  for (let i = 0; i < 9; i++) {
    const x = 60 + rnd() * 960, y = 60 + rnd() * 840, o = rnd() > 0.5;
    s += o ? `<circle cx="${x}" cy="${y}" r="22" />` : `<path d="M${x - 20} ${y - 20}L${x + 20} ${y + 20}M${x + 20} ${y - 20}L${x - 20} ${y + 20}"/>`;
  }
  for (let i = 0; i < 3; i++) {
    const x1 = 100 + rnd() * 880, y1 = 600 + rnd() * 300, x2 = x1 + (rnd() - .5) * 400, y2 = y1 - 200 - rnd() * 200;
    s += `<path d="M${x1} ${y1} Q ${(x1 + x2) / 2 + 120} ${(y1 + y2) / 2} ${x2} ${y2}" stroke-dasharray="14 12"/><circle cx="${x2}" cy="${y2}" r="7" fill="rgba(255,255,255,.18)"/>`;
  }
  return `<svg width="1080" height="960" style="position:absolute;inset:0" fill="none" stroke="rgba(255,255,255,.13)" stroke-width="6" stroke-linecap="round">${s}</svg>`;
}

function board(b, i) {
  return `<!doctype html><html><head><meta charset="utf-8"><style>
  *{margin:0;box-sizing:border-box}
  body{width:1080px;height:960px;overflow:hidden;font-family:'Inter',sans-serif;color:#fff;
   background:radial-gradient(ellipse at 50% 40%,#2f5d3e 0%,#1d3b28 55%,#0f2216 100%)}
  .frame{position:absolute;inset:18px;border:14px solid #6b4a2b;border-radius:10px;box-shadow:inset 0 0 80px rgba(0,0,0,.55)}
  .wrap{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:220px 70px 60px}
  .icon{font-family:'Noto Color Emoji';font-size:210px;line-height:1;filter:drop-shadow(0 14px 18px rgba(0,0,0,.45))}
  .label{margin-top:34px;font-weight:900;font-size:${b.label.length > 20 ? 66 : 84}px;line-height:1;text-transform:uppercase;letter-spacing:-1px;
    color:#fff;text-shadow:0 0 2px #fff,0 6px 0 rgba(0,0,0,.35)}
  .sub{margin-top:22px;font-weight:700;font-size:40px;color:#ffe066}
  .tag{position:absolute;right:52px;bottom:46px;font-weight:800;font-size:24px;letter-spacing:4px;color:rgba(255,255,255,.45)}
  </style></head><body>${chalk(i + 3)}<div class="frame"></div>
  <div class="wrap"><div class="icon">${b.icon}</div><div class="label">${esc(b.label)}</div><div class="sub">${esc(b.sub)}</div></div>
  <div class="tag">FILM ROOM · ${String(i + 1).padStart(2, '0')}</div></body></html>`;
}

function hook(text) {
  return `<!doctype html><html><head><meta charset="utf-8"><style>
  *{margin:0}html,body{background:transparent}
  body{display:inline-block;font-family:'Inter',sans-serif}
  .b{display:inline-block;background:#fff;color:#111;font-weight:700;font-size:54px;padding:16px 30px;border-radius:18px;box-shadow:0 8px 24px rgba(0,0,0,.35)}
  .b i{font-style:normal;font-family:'Noto Color Emoji'}
  </style></head><body><div class="b" id="b">${esc(text).replace(/(\p{Extended_Pictographic}+)/gu, '<i>$1</i>')}</div></body></html>`;
}

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1080, height: 960 } });
  for (const [i, beat] of script.beats.entries()) {
    await page.setContent(board(beat.board, i));
    await page.evaluate(() => document.fonts.ready);
    await page.screenshot({ path: path.join(out, `b${String(i).padStart(2, '0')}.png`) });
  }
  if (script.hook_text) {
    await page.setContent(hook(script.hook_text));
    await page.evaluate(() => document.fonts.ready);
    await page.locator('#b').screenshot({ path: path.join(out, 'hook.png'), omitBackground: true });
  }
  await browser.close();
  console.log('boards rendered');
})();
