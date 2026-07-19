"""HTML/CSS/JS page template (build_html)."""
import json

from assets import HLJS_JS, HLJS_THEMES, MARKDOWN_IT_JS
from config import APP_VERSION, PRESETS, _is_windows_dark_theme

def build_html(config: dict) -> str:
    presets_json      = json.dumps(HLJS_THEMES)
    presets_list_json = json.dumps(PRESETS)
    stored_theme      = config.get('theme', 'dark')
    init_theme        = stored_theme if stored_theme != 'system' else ('dark' if _is_windows_dark_theme() else 'light')
    init_preset       = config['preset']
    version           = APP_VERSION

    return (
        """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style id="hljs-theme"></style>
<style>
:root {
  --bg:#1e1e2e;--fg:#cdd6f4;--heading:#cba6f7;--link:#89b4fa;
  --code-bg:#313244;--border:#45475a;--muted:#6c7086;
  --menu-bg:#2a2a3e;--menu-border:#45475a;--menu-hover:#313244;--menu-fg:#cdd6f4;
}
[data-theme="light"] {
  --bg:#ffffff;--fg:#24292f;--heading:#6639ba;--link:#0969da;
  --code-bg:#f6f8fa;--border:#d0d7de;--muted:#57606a;
  --menu-bg:#ffffff;--menu-border:#d0d7de;--menu-hover:#f6f8fa;--menu-fg:#24292f;
}
*{box-sizing:border-box;margin:0;padding:0}
html,body{height:100%}
body{
  background:var(--bg);color:var(--fg);
  font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
  font-size:15px;line-height:1.7;
  -webkit-app-region:drag;user-select:none;
}
#page{max-width:956px;margin:0 auto;padding:36px 48px 64px;-webkit-app-region:drag}
#page a,#page code,#page pre,#page table,#page input,#page img{
  -webkit-app-region:no-drag;user-select:text;
}
#controls{
  position:fixed;top:8px;right:10px;display:flex;gap:4px;
  opacity:0;transition:opacity .2s;z-index:200;-webkit-app-region:no-drag;
}
body:hover #controls{opacity:1}

#version{
  position:fixed;bottom:6px;left:10px;font-size:10px;color:var(--muted);
  opacity:0;transition:opacity .2s;z-index:150;-webkit-app-region:no-drag;
  pointer-events:none;
}
body:hover #version{opacity:0.6}

/* Lightweight image lightbox */
#img-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.85);
  display: none; align-items: center; justify-content: center; z-index: 9999;
  cursor: zoom-out;
}
#img-overlay img {
  max-width: 95vw; max-height: 95vh; object-fit: contain;
  box-shadow: 0 10px 40px rgba(0,0,0,0.6);
}

/* Search highlight */
mark.search-hit {
  background: #f9d71c;
  color: #222;
  border-radius: 2px;
  padding: 0 1px;
}
mark.search-current {
  background: #f77d05;
  color: white;
}

.ctrl-btn{
  background:rgba(128,128,128,.15);border:none;border-radius:5px;
  color:var(--fg);cursor:pointer;font-size:14px;line-height:1;
  padding:5px 9px;-webkit-app-region:no-drag;transition:background .15s;
}
.ctrl-btn:hover{background:rgba(128,128,128,.35)}
#ctx-menu{
  position:fixed;background:var(--menu-bg);border:1px solid var(--menu-border);
  border-radius:8px;box-shadow:0 8px 28px rgba(0,0,0,.35);
  padding:5px 0;min-width:190px;z-index:1000;-webkit-app-region:no-drag;
}
.ctx-item{cursor:pointer;font-size:13px;padding:6px 14px;color:var(--menu-fg);white-space:nowrap}
.ctx-item:hover{background:var(--menu-hover)}
.ctx-item.active{font-weight:600}
.ctx-divider{border-top:1px solid var(--menu-border);margin:4px 0}
.ctx-label{font-size:10px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);padding:4px 14px 2px}
h1,h2,h3,h4,h5,h6{color:var(--heading);margin:1.4em 0 .5em;font-weight:600}
h1{font-size:2em;margin-top:.6em}
h2{font-size:1.5em;border-bottom:1px solid var(--border);padding-bottom:.3em}
h3{font-size:1.25em}
p{margin:.8em 0}
a{color:var(--link);text-decoration:none}
a:hover{text-decoration:underline}
ul,ol{margin:.6em 0 .6em 1.6em}
li{margin:.2em 0}
blockquote{border-left:3px solid var(--border);color:var(--muted);margin:1em 0;padding:.3em 1em}
code{
  background:var(--code-bg);border-radius:4px;
  font-family:'Cascadia Code','Fira Code','Consolas',monospace;
  font-size:.88em;padding:.15em .4em;
  -webkit-app-region:no-drag;user-select:text;
}
pre{
  background:var(--code-bg);border-radius:8px;margin:1em 0;
  overflow-x:auto;padding:1em 1.2em;
  -webkit-app-region:no-drag;user-select:text;
}
pre code{background:none;font-size:.9em;padding:0}
table{border-collapse:collapse;margin:1em 0;width:100%}
th,td{border:1px solid var(--border);padding:.5em .9em;text-align:left}
th{background:var(--code-bg);font-weight:600}
tr:nth-child(even) td{background:rgba(128,128,128,.05)}
img{max-width:100%;border-radius:4px}
hr{border:none;border-top:1px solid var(--border);margin:1.5em 0}
input[type="checkbox"]{margin-right:.4em;-webkit-app-region:no-drag}
/* Floating auto-hiding scrollbar — overlay only, no track, fades in on use */
::-webkit-scrollbar{width:8px;height:8px;background:transparent}
::-webkit-scrollbar-track{background:transparent;border:none}
::-webkit-scrollbar-thumb{
  background:transparent;
  border-radius:8px;
  border:none;
  transition:background .25s ease;
}
::-webkit-scrollbar-corner{background:transparent}
/* Reveal thumb while actively scrolling OR pointer is over content */
html.scrolling ::-webkit-scrollbar-thumb,
body:hover ::-webkit-scrollbar-thumb{background:rgba(128,128,128,.3)}
html.scrolling ::-webkit-scrollbar-thumb:hover,
body:hover ::-webkit-scrollbar-thumb:hover{background:rgba(128,128,128,.55)}
html{scrollbar-width:thin;scrollbar-color:transparent transparent;transition:scrollbar-color .25s}
html.scrolling,html:hover{scrollbar-color:rgba(128,128,128,.3) transparent}
</style>
</head>
<body data-theme="__THEME__">
<div id="controls">
  <button class="ctrl-btn" id="btn-tall"  title="Doc width, full height">&#9647;</button>
  <button class="ctrl-btn" id="btn-left"  title="Snap left half">&#9703;</button>
  <button class="ctrl-btn" id="btn-right" title="Snap right half">&#9704;</button>
  <button class="ctrl-btn" id="btn-full"  title="Fullscreen (F11)">&#9974;</button>
  <button class="ctrl-btn" id="btn-gear"  title="Settings">&#9881;</button>
  <button class="ctrl-btn" id="btn-close" title="Close">&#10005;</button>
</div>
<div id="page"><div id="content"></div></div>
<div id="ctx-menu" hidden></div>
<div id="version">v__VERSION__</div>
<div id="img-overlay"><img alt=""></div>

<!-- Lightweight in-document search -->
<div id="search-bar" style="display:none;position:fixed;top:8px;left:50%;transform:translateX(-50%);z-index:1000;background:var(--menu-bg);border:1px solid var(--menu-border);border-radius:6px;padding:4px 8px;box-shadow:0 4px 12px rgba(0,0,0,0.3);font-size:13px;">
  <input id="search-input" placeholder="Search..." style="background:transparent;border:none;outline:none;color:var(--menu-fg);width:220px;">
  <span id="search-count" style="margin:0 6px;color:var(--muted);font-size:11px;"></span>
  <button id="search-prev" style="background:none;border:none;color:var(--menu-fg);cursor:pointer;">↑</button>
  <button id="search-next" style="background:none;border:none;color:var(--menu-fg);cursor:pointer;">↓</button>
  <button id="search-close" style="background:none;border:none;color:var(--muted);cursor:pointer;margin-left:4px;">✕</button>
</div>
<script>__MARKDOWN_IT_JS__</script>
<script>__HLJS_JS__</script>
<script>
const THEMES = __PRESETS_JSON__;
const PRESETS = __PRESETS_LIST_JSON__;

let currentTheme  = '__STORED_THEME__';   // can be 'dark', 'light', or 'system'
let currentPreset = '__PRESET__';

const hljsStyle = document.getElementById('hljs-theme');
const ctxMenu   = document.getElementById('ctx-menu');

// THEME-CYCLE-LOGIC-START
function effectiveTheme(t) {
  if (t !== 'system') return t;
  const isDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
  return isDark ? 'dark' : 'light';
}

// Cycle dark -> light -> system -> dark, skipping any state that would look
// identical to the current appearance — every click must visibly change the page.
function nextTheme() {
  const order = {dark: ['light', 'system'], light: ['system', 'dark'], system: ['dark', 'light']};
  const cur = effectiveTheme(currentTheme);
  for (const cand of (order[currentTheme] || ['dark', 'light'])) {
    if (effectiveTheme(cand) !== cur) return cand;
  }
  return cur === 'dark' ? 'light' : 'dark';
}
// THEME-CYCLE-LOGIC-END

function setTheme(t) {
  currentTheme = t;
  document.body.dataset.theme = effectiveTheme(t);
  persistSettings();
}

function setPreset(key) {
  currentPreset = key;
  hljsStyle.textContent = THEMES[key] || '';
  ctxMenu.querySelectorAll('.preset-item').forEach(el => {
    el.textContent = (el.dataset.key === key ? '\\u2713  ' : '    ') + el.dataset.label;
    el.classList.toggle('active', el.dataset.key === key);
  });
  persistSettings();
}

function persistSettings() {
  if (window.pywebview && window.pywebview.api && window.pywebview.api.save_config) {
    pywebview.api.save_config({theme: currentTheme, preset: currentPreset});
  }
}

if (window.matchMedia) {
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
    if (currentTheme === 'system') {
      document.body.dataset.theme = effectiveTheme('system');
    }
  });
}

async function buildMenu(x, y) {
  ctxMenu.replaceChildren();

  // Theme row
  // Label names the *next* state from nextTheme(), which skips visual no-ops.
  const themeItem = document.createElement('div');
  themeItem.className = 'ctx-item';
  const nextT = nextTheme();
  if (nextT === 'light') {
    themeItem.textContent = '\\u2600  Switch to Light';
  } else if (nextT === 'system') {
    themeItem.textContent = '\\u2699\\uFE0F  Follow System';
  } else {
    themeItem.textContent = '\\uD83C\\uDF19  Switch to Dark';
  }
  themeItem.onclick = () => {
    setTheme(nextT);
    closeMenu();
  };
  ctxMenu.appendChild(themeItem);

  ctxMenu.appendChild(Object.assign(document.createElement('div'), {className: 'ctx-divider'}));

  // Recent files (lightweight). pywebview API calls return Promises — must await.
  const recent = (window.pywebview && window.pywebview.api && window.pywebview.api.get_recent_files)
    ? await window.pywebview.api.get_recent_files() : [];
  if (recent.length > 0) {
    const recentLbl = document.createElement('div');
    recentLbl.className = 'ctx-label';
    recentLbl.textContent = 'Recent';
    ctxMenu.appendChild(recentLbl);

    recent.forEach(p => {
      const item = document.createElement('div');
      item.className = 'ctx-item';
      const name = p.split(/[\\/]/).pop();
      item.textContent = '  ' + name;
      item.title = p;
      item.onclick = () => {
        closeMenu();
        if (window.pywebview && window.pywebview.api && window.pywebview.api.open_recent) {
          pywebview.api.open_recent(p);
        }
      };
      ctxMenu.appendChild(item);
    });

    ctxMenu.appendChild(Object.assign(document.createElement('div'), {className: 'ctx-divider'}));
  }

  const lbl = document.createElement('div');
  lbl.className = 'ctx-label';
  lbl.textContent = 'Syntax Theme';
  ctxMenu.appendChild(lbl);

  PRESETS.forEach(([key, label]) => {
    const item = document.createElement('div');
    item.className = 'ctx-item preset-item';
    item.dataset.key   = key;
    item.dataset.label = label;
    item.textContent   = (key === currentPreset ? '\\u2713  ' : '    ') + label;
    if (key === currentPreset) item.classList.add('active');
    item.onclick = () => { setPreset(key); closeMenu(); };
    ctxMenu.appendChild(item);
  });

  ctxMenu.hidden = false;
  const mw = ctxMenu.offsetWidth, mh = ctxMenu.offsetHeight;
  ctxMenu.style.left = Math.min(x, window.innerWidth  - mw - 8) + 'px';
  ctxMenu.style.top  = Math.min(y, window.innerHeight - mh - 8) + 'px';
}

function closeMenu() { ctxMenu.hidden = true; }

document.addEventListener('contextmenu', e => { e.preventDefault(); buildMenu(e.clientX, e.clientY); });
document.addEventListener('click', e => { if (!ctxMenu.contains(e.target)) closeMenu(); });
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') closeMenu();
  if (e.key === 'F11') { e.preventDefault(); pywebview.api.toggle_fullscreen(); }
});

// Lightweight drag & drop support for .md files
document.addEventListener('dragover', e => {
  e.preventDefault();
  e.dataTransfer.dropEffect = 'copy';
});
document.addEventListener('drop', e => {
  e.preventDefault();
  const file = e.dataTransfer.files[0];
  if (!file) return;
  if (!file.name.toLowerCase().endsWith('.md') && !file.name.toLowerCase().endsWith('.markdown')) {
    return;
  }
  const reader = new FileReader();
  reader.onload = () => {
    if (window.pywebview && window.pywebview.api && window.pywebview.api.load_dropped_file) {
      pywebview.api.load_dropped_file(file.name, reader.result);
    }
  };
  reader.readAsText(file);
});

// === Lightweight in-document search (Ctrl+F) ===
(function() {
  const bar = document.getElementById('search-bar');
  const input = document.getElementById('search-input');
  const countEl = document.getElementById('search-count');
  const btnPrev = document.getElementById('search-prev');
  const btnNext = document.getElementById('search-next');
  const btnClose = document.getElementById('search-close');

  if (!bar || !input) return;

  let matches = [];
  let currentIndex = -1;

  function clearHighlights() {
    document.querySelectorAll('mark.search-hit, mark.search-current').forEach(m => {
      const parent = m.parentNode;
      parent.replaceChild(document.createTextNode(m.textContent), m);
      parent.normalize();
    });
    matches = [];
    currentIndex = -1;
    if (countEl) countEl.textContent = '';
  }

  function doSearch() {
    clearHighlights();
    const term = input.value.trim();
    if (!term) return;

    const walker = document.createTreeWalker(
      document.getElementById('content'),
      NodeFilter.SHOW_TEXT,
      null
    );

    const found = [];
    let node;
    while ((node = walker.nextNode())) {
      const text = node.nodeValue;
      const lower = text.toLowerCase();
      let pos = 0;
      while ((pos = lower.indexOf(term.toLowerCase(), pos)) !== -1) {
        found.push({ node, start: pos, length: term.length });
        pos += term.length;
      }
    }

    // Wrap matches
    found.reverse().forEach(hit => {
      const { node, start, length } = hit;
      const before = node.nodeValue.slice(0, start);
      const match = node.nodeValue.slice(start, start + length);
      const after = node.nodeValue.slice(start + length);

      const mark = document.createElement('mark');
      mark.className = 'search-hit';
      mark.textContent = match;

      const frag = document.createDocumentFragment();
      if (before) frag.appendChild(document.createTextNode(before));
      frag.appendChild(mark);
      if (after) frag.appendChild(document.createTextNode(after));

      node.parentNode.replaceChild(frag, node);
    });

    matches = Array.from(document.querySelectorAll('mark.search-hit'));
    currentIndex = matches.length ? 0 : -1;
    updateCurrent();
  }

  function updateCurrent() {
    matches.forEach((m, i) => m.classList.toggle('search-current', i === currentIndex));
    if (countEl) {
      countEl.textContent = matches.length ? `${currentIndex + 1}/${matches.length}` : '';
    }
    if (currentIndex >= 0) {
      matches[currentIndex].scrollIntoView({ block: 'center', behavior: 'smooth' });
    }
  }

  function next() {
    if (!matches.length) return;
    currentIndex = (currentIndex + 1) % matches.length;
    updateCurrent();
  }
  function prev() {
    if (!matches.length) return;
    currentIndex = (currentIndex - 1 + matches.length) % matches.length;
    updateCurrent();
  }

  function closeSearch() {
    bar.style.display = 'none';
    clearHighlights();
    input.value = '';
  }

  // Keyboard trigger
  document.addEventListener('keydown', e => {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'f') {
      e.preventDefault();
      bar.style.display = 'block';
      input.focus();
      input.select();
    }
    if (e.key === 'Escape' && bar.style.display !== 'none') {
      closeSearch();
    }
    if (e.key === 'Enter' && document.activeElement === input) {
      e.preventDefault();
      if (matches.length === 0) doSearch();
      else next();
    }
  });

  let _searchDebounce = null;
  input.addEventListener('input', () => {
    clearTimeout(_searchDebounce);
    _searchDebounce = setTimeout(() => {
      if (input.value.trim().length >= 2) {
        doSearch();
      } else {
        clearHighlights();
      }
    }, 150);
  });

  btnNext && btnNext.addEventListener('click', next);
  btnPrev && btnPrev.addEventListener('click', prev);
  btnClose && btnClose.addEventListener('click', closeSearch);
})();

// Simple image lightbox (click any rendered image to enlarge)
const imgOverlay = document.getElementById('img-overlay');
const overlayImg = imgOverlay ? imgOverlay.querySelector('img') : null;

document.addEventListener('click', e => {
  if (e.target.tagName === 'IMG' && e.target.closest('#content') && overlayImg) {
    overlayImg.src = e.target.src;
    imgOverlay.style.display = 'flex';
  }
});
if (imgOverlay) {
  imgOverlay.addEventListener('click', () => { imgOverlay.style.display = 'none'; });
}
document.addEventListener('keydown', e => {
  if (e.key === 'Escape' && imgOverlay && imgOverlay.style.display === 'flex') {
    imgOverlay.style.display = 'none';
  }
});

document.getElementById('btn-gear').addEventListener('click', e => {
  e.stopPropagation();
  const r = e.currentTarget.getBoundingClientRect();
  buildMenu(r.left, r.bottom + 4);
});

document.getElementById('btn-close').addEventListener('mousedown', (e) => {
  e.stopPropagation();
});
document.getElementById('btn-close').addEventListener('click', () => {
  pywebview.api.close_window();
});

document.getElementById('btn-tall').addEventListener('click', () => {
  pywebview.api.snap('reading');
});

document.getElementById('btn-left').addEventListener('click',  () => pywebview.api.snap('left'));
document.getElementById('btn-right').addEventListener('click', () => pywebview.api.snap('right'));
document.getElementById('btn-full').addEventListener('click',  () => pywebview.api.toggle_fullscreen());
// Window movement: pywebview easy_drag handles drag via -webkit-app-region: drag.
// Window resize: native Win32 (WS_THICKFRAME added on load, OS handles edges).

const md = markdownit({
  html: false,
  linkify: true,
  typographer: true,
  highlight: (str, lang) => {
    let body;
    if (lang && hljs.getLanguage(lang)) {
      try { body = hljs.highlight(str, {language: lang, ignoreIllegals: true}).value; } catch (_) {}
    }
    if (!body) body = hljs.highlightAuto(str).value;
    return '<pre class="hljs"><code>' + body + '</code></pre>';
  }
});

function jslog(msg) {
  try { if (window.pywebview && window.pywebview.api && window.pywebview.api.js_log) pywebview.api.js_log(String(msg)); } catch(_) {}
  console.log(msg);
}

// Relative img src cannot load against an HTML-string page (no file base URL).
// Ask Python to embed local files as data URIs relative to the open .md path.
async function resolveContentImages(root) {
  if (!root || !window.pywebview || !window.pywebview.api) return;
  if (typeof pywebview.api.resolve_media !== 'function') return;
  const imgs = root.querySelectorAll('img[src]');
  for (const img of imgs) {
    const src = img.getAttribute('src');
    if (!src) continue;
    try {
      const resolved = await pywebview.api.resolve_media(src);
      if (resolved && resolved !== src) img.setAttribute('src', resolved);
    } catch (e) {
      jslog('resolve_media failed for ' + src + ': ' + e);
    }
  }
}

async function reloadFromDisk() {
  const contentEl = document.getElementById('content');
  if (!contentEl) return;
  try {
    const raw = await pywebview.api.get_file();
    const rendered = md.render(raw);
    const frag = document.createRange().createContextualFragment(rendered);
    contentEl.replaceChildren(frag);
    await resolveContentImages(contentEl);
  } catch (e) {
    jslog('reloadFromDisk failed: ' + e);
  }
}

async function init() {
  jslog('init() entered');
  const contentEl = document.getElementById('content');
  try {
    jslog('init: calling get_file');
    const raw = await pywebview.api.get_file();
    jslog('init: got ' + raw.length + ' bytes');
    const rendered = md.render(raw);
    jslog('init: rendered ' + rendered.length + ' chars of HTML');
    const frag = document.createRange().createContextualFragment(rendered);
    contentEl.replaceChildren(frag);
    await resolveContentImages(contentEl);
    setPreset(currentPreset);
    setTheme(currentTheme);
    jslog('init: done');
  } catch (e) {
    jslog('init FAILED: ' + e);
    const errEl = Object.assign(document.createElement('p'), {
      textContent: 'Failed to load file: ' + e,
    });
    errEl.style.cssText = 'color:var(--muted);padding:2em';
    contentEl.replaceChildren(errEl);
  }
}

// Robust init triggering: event listener + polling + failsafe.
// pywebviewready may have already fired before this script ran, so we poll too.
let _inited = false;
function tryInit() {
  if (_inited) return;
  if (window.pywebview && window.pywebview.api && typeof window.pywebview.api.get_file === 'function') {
    _inited = true;
    init();
  }
}
// Auto-hide scrollbar: add `scrolling` class while wheel/scroll happens, clear after pause
let _scrollHideTimer = null;
function markScrolling() {
  document.documentElement.classList.add('scrolling');
  clearTimeout(_scrollHideTimer);
  _scrollHideTimer = setTimeout(() => {
    document.documentElement.classList.remove('scrolling');
  }, 900);
}
window.addEventListener('scroll', markScrolling, {passive: true});
window.addEventListener('wheel',  markScrolling, {passive: true});

window.addEventListener('pywebviewready', tryInit);
let _polls = 0;
const _pollId = setInterval(() => {
  _polls++;
  tryInit();
  if (_inited || _polls > 200) clearInterval(_pollId);
}, 50);

// Re-apply thickframe on focus regain (debounced — avoids fighting the first click).
let _focusRefreshTimer = null;
window.addEventListener('focus', () => {
  clearTimeout(_focusRefreshTimer);
  _focusRefreshTimer = setTimeout(() => {
    if (window.pywebview && window.pywebview.api && window.pywebview.api.refresh_resize_handles) {
      pywebview.api.refresh_resize_handles();
    }
  }, 50);
});

// On mousedown in the button area (except close), explicitly activate the window.
const controls = document.getElementById('controls');
if (controls) {
  controls.addEventListener('mousedown', (e) => {
    if (e.target.closest('#btn-close')) return;
    if (window.pywebview && window.pywebview.api && window.pywebview.api.force_activate) {
      pywebview.api.force_activate();
    }
  }, { capture: true });
}

setTimeout(() => {
  if (!_inited) {
    document.getElementById('content').textContent =
      'pywebview API never became available after 10s. Check pywebview installation.';
  }
}, 10000);
</script>
</body>
</html>"""
        .replace('__MARKDOWN_IT_JS__', MARKDOWN_IT_JS)
        .replace('__HLJS_JS__',        HLJS_JS)
        .replace('__PRESETS_JSON__',      presets_json)
        .replace('__PRESETS_LIST_JSON__', presets_list_json)
        .replace('__THEME__',        init_theme)
        .replace('__STORED_THEME__', stored_theme)
        .replace('__PRESET__',       init_preset)
        .replace('__VERSION__',      version)
    )
