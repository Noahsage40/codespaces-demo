// Renders one PNG per scene from a video's script.json.
// Usage: node pipeline/render_slides.js videos/2015-qbs [--vertical]
const fs = require('fs'), path = require('path');
const { chromium } = require('playwright');

const dir = path.resolve(process.argv[2]);
const vertical = process.argv.includes('--vertical');
const W = vertical ? 1080 : 1920, H = vertical ? 1920 : 1080;
const script = JSON.parse(fs.readFileSync(path.join(dir, 'script.json'), 'utf8'));
const outDir = path.join(dir, vertical ? 'slides-vertical' : 'slides');
fs.mkdirSync(outDir, { recursive: true });

const esc = s => String(s ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;');
function img(file) {
  if (!file) return null;
  const p = path.join(dir, 'images', file);
  if (!fs.existsSync(p) || fs.readFileSync(p).slice(0, 15).toString().includes('<')) return null;
  return 'data:image/jpeg;base64,' + fs.readFileSync(p).toString('base64');
}
const initials = n => n.split(' ').map(w => w[0]).join('');
const stars = n => '★'.repeat(n) + '<span class="dim">' + '★'.repeat(5 - n) + '</span>';
function portrait(s, cls = 'portrait') {
  const src = img(s.img);
  return src ? `<div class="${cls}" style="background-image:url('${src}')"></div>`
             : `<div class="${cls} ph"><span>${esc(initials(s.name || '?'))}</span></div>`;
}

const CSS = `
*{margin:0;box-sizing:border-box}
body{width:${W}px;height:${H}px;overflow:hidden;font-family:'Inter',sans-serif;color:#fff;
 background:radial-gradient(ellipse at 30% 20%,#1d2b55 0%,#0b1020 60%,#05070f 100%)}
.field{position:absolute;inset:0;background:repeating-linear-gradient(90deg,transparent 0 ${W / 10 - 2}px,rgba(255,255,255,.05) ${W / 10 - 2}px ${W / 10}px)}
.stage{position:absolute;inset:0;padding:${vertical ? '170px 70px 420px' : '90px 110px 190px'};display:flex;flex-direction:column}
.kicker{color:#f5c542;font-weight:800;letter-spacing:6px;font-size:${vertical ? 34 : 30}px;text-transform:uppercase}
.h1{font-weight:900;text-transform:uppercase;line-height:.95;letter-spacing:-2px}
.gold{color:#f5c542}.dim{color:rgba(255,255,255,.18)}
.portrait{background:center 25%/cover no-repeat;border-radius:28px;box-shadow:0 30px 80px rgba(0,0,0,.6);border:4px solid rgba(255,255,255,.12)}
.ph{background:linear-gradient(145deg,#2a3a70,#141c38);display:flex;align-items:center;justify-content:center}
.ph span{font-weight:900;font-size:180px;color:rgba(255,255,255,.25);letter-spacing:-6px}
.pill{display:inline-block;background:#f5c542;color:#0b1020;font-weight:900;padding:10px 22px;border-radius:12px;letter-spacing:2px;text-transform:uppercase}
.row{display:flex;gap:${vertical ? 40 : 70}px;align-items:center;flex:1}
.col{display:flex;flex-direction:column;gap:22px}
.meta{font-size:${vertical ? 40 : 36}px;font-weight:600;color:rgba(255,255,255,.85)}
.meta b{color:#f5c542;font-weight:800}
.stars{font-size:${vertical ? 64 : 60}px;color:#f5c542;letter-spacing:6px}
`;

function slideHTML(s) {
  let body = '';
  const big = (v, h) => (vertical ? v : h);
  switch (s.type) {
    case 'title':
      body = `<div class="stage" style="justify-content:center;align-items:${big('center', 'flex-start')};text-align:${big('center', 'left')}">
        <div class="kicker">${esc(s.kicker)}</div>
        <div class="h1" style="text-transform:none;font-size:${big(110, 128)}px;margin:26px 0 30px;max-width:${big(940, 1500)}px">${esc(s.title).replace(/(TOP|QBs\??)/g, '<span class="gold">$1</span>')}</div>
        <div class="meta">${esc(s.sub)}</div></div>`;
      break;
    case 'lineup': {
      const cards = s.players.map((p, i) => `<div style="display:flex;flex-direction:column;gap:12px;align-items:center">
        ${portrait(p, 'portrait')}<div style="font-weight:900;font-size:${big(30, 28)}px;text-transform:uppercase;text-align:center">${esc(p.name)}</div>
        <div class="pill" style="font-size:${big(20, 18)}px;padding:6px 14px">${esc(p.tag)}</div></div>`).join('');
      body = `<div class="stage"><div class="kicker">The lineup · Class of 2015</div>
        <div style="flex:1;display:grid;grid-template-columns:repeat(${big(2, 4)},1fr);gap:${big('34px 40px', '30px 50px')};margin-top:40px;align-content:center">${cards}</div></div>
        <style>.portrait{width:${big(260, 250)}px;height:${big(260, 250)}px;border-radius:50%}.ph span{font-size:90px}</style>`;
      break;
    }
    case 'recruit':
      body = `<div class="stage"><div class="kicker">Class of 2015 recruit</div>
        <div class="row" style="flex-direction:${big('column', 'row')};justify-content:center">
          ${portrait(s)}
          <div class="col" style="align-items:${big('center', 'flex-start')};text-align:${big('center', 'left')}">
            <div class="pill" style="font-size:30px">${esc(s.rank)}</div>
            <div class="h1" style="font-size:${big(110, 130)}px">${esc(s.name)}</div>
            <div class="stars">${stars(s.stars)}</div>
            <div class="meta">${esc(s.school)}</div>
            <div class="meta">Signed: <b>${esc(s.commit)}</b></div>
          </div></div></div>
        <style>.portrait{width:${big(620, 560)}px;height:${big(620, 640)}px}</style>`;
      break;
    case 'path': {
      const steps = s.steps.map((t, i) => `<div style="display:flex;align-items:center;gap:${big(0, 26)}px;flex-direction:${big('column', 'row')}">
        <div style="background:${i === s.steps.length - 1 ? '#f5c542' : 'rgba(255,255,255,.1)'};color:${i === s.steps.length - 1 ? '#0b1020' : '#fff'};border:3px solid rgba(255,255,255,.2);border-radius:22px;padding:${big('26px 40px', '34px 38px')};font-weight:900;font-size:${big(56, 50)}px;text-transform:uppercase;white-space:nowrap">
        <span style="opacity:.55;font-size:.6em;margin-right:14px">${i + 1}</span>${esc(t)}</div>
        ${i < s.steps.length - 1 ? `<div style="font-size:${big(60, 54)}px;color:#f5c542;font-weight:900;padding:${big('10px 0', '0')}">${big('↓', '→')}</div>` : ''}</div>`).join('');
      body = `<div class="stage"><div class="kicker">${esc(s.name)} · the path</div>
        <div style="flex:1;display:flex;flex-direction:${big('column', 'row')};align-items:center;justify-content:center;gap:${big(0, 26)}px;flex-wrap:wrap">${steps}</div></div>`;
      break;
    }
    case 'big': {
      const src = img(s.img);
      body = `${src ? `<div style="position:absolute;inset:0;background:url('${src}') center 25%/cover;opacity:.22;filter:grayscale(.4)"></div>` : ''}
        <div class="stage" style="justify-content:center;align-items:center;text-align:center">
        <div class="kicker">${esc(s.eyebrow)}</div>
        <div class="h1 gold" style="font-size:${big(140, 170)}px;margin:30px 0;max-width:${big(960, 1700)}px;text-shadow:0 10px 40px rgba(0,0,0,.6)">${esc(s.big)}</div>
        <div class="meta" style="font-size:${big(44, 44)}px">${esc(s.small)}</div></div>`;
      break;
    }
    case 'now': {
      const pts = s.points.map(p => `<div class="meta" style="display:flex;gap:18px;align-items:center"><span style="color:#f5c542;font-size:.9em">▶</span>${esc(p)}</div>`).join('');
      body = `<div class="stage"><div class="kicker">Where are they now?</div>
        <div class="row" style="flex-direction:${big('column', 'row')};justify-content:center">
          ${portrait(s)}
          <div class="col" style="align-items:${big('center', 'flex-start')}">
            <div class="h1" style="font-size:${big(90, 96)}px">${esc(s.name)}</div>
            <div style="background:#e0263c;color:#fff;font-weight:900;font-size:${big(64, 70)}px;padding:12px 30px;border-radius:16px;text-transform:uppercase;letter-spacing:1px">${esc(s.verdict)}</div>
            <div class="col" style="gap:14px;margin-top:10px">${pts}</div>
          </div></div></div>
        <style>.portrait{width:${big(520, 480)}px;height:${big(560, 600)}px}</style>`;
      break;
    }
    case 'outro': {
      const pts = s.points.map(p => `<div class="meta" style="font-size:${big(46, 44)}px;display:flex;gap:18px"><span class="gold">✓</span>${esc(p)}</div>`).join('');
      body = `<div class="stage" style="justify-content:center;align-items:${big('center', 'flex-start')}">
        <div class="kicker">Final tally</div>
        <div class="h1" style="font-size:${big(100, 120)}px;margin:24px 0 40px">${esc(s.title)}</div>
        <div class="col" style="gap:18px">${pts}</div>
        <div class="pill" style="margin-top:50px;font-size:34px">${esc(s.sub)}</div></div>`;
      break;
    }
  }
  return `<!doctype html><html><head><meta charset="utf-8"><style>${CSS}</style></head><body><div class="field"></div>${body}</body></html>`;
}

// Transparent lower-third banner shown over game footage
function lowerHTML(s) {
  const title = s.name || s.big || s.title || '';
  const sub = s.eyebrow || s.rank || s.verdict || '';
  return `<!doctype html><html><head><meta charset="utf-8"><style>${CSS}
  body{background:transparent!important}
  .lt{position:absolute;left:${vertical ? 60 : 90}px;bottom:${vertical ? 520 : 170}px;display:flex;flex-direction:column;align-items:flex-start;gap:0}
  .lt .t{background:#0b1020;color:#fff;font-weight:900;font-size:${vertical ? 64 : 58}px;padding:12px 26px;text-transform:uppercase;border-left:12px solid #f5c542}
  .lt .s{background:#f5c542;color:#0b1020;font-weight:800;font-size:${vertical ? 32 : 28}px;padding:8px 26px;letter-spacing:3px;text-transform:uppercase}
  </style></head><body><div class="lt"><div class="t">${esc(title)}</div>${sub ? `<div class="s">${esc(sub)}</div>` : ''}</div></body></html>`;
}

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: W, height: H } });
  for (const [i, sc] of script.scenes.entries()) {
    await page.setContent(slideHTML(sc.slide));
    await page.evaluate(() => document.fonts.ready);
    await page.screenshot({ path: path.join(outDir, String(i).padStart(2, '0') + '.png') });
    if (sc.broll) {
      await page.setContent(lowerHTML(sc.slide));
      await page.evaluate(() => document.fonts.ready);
      await page.screenshot({ path: path.join(outDir, String(i).padStart(2, '0') + '_lower.png'), omitBackground: true });
    }
  }
  await browser.close();
  console.log(`rendered ${script.scenes.length} slides → ${outDir}`);
})();
