"""HTML/CSS/JS page template (build_html)."""
import json

from assets import HLJS_JS, HLJS_THEMES, MARKDOWN_IT_JS
from config import APP_VERSION, THEMES

def build_html(config: dict) -> str:
    hljs_json       = json.dumps(HLJS_THEMES)
    themes_list_json = json.dumps(THEMES)
    init_theme      = config.get('theme', 'github-dark')
    version         = APP_VERSION

    return (
        """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style id="hljs-theme"></style>
<style>
/* App chrome palettes — one full look per theme key (matches highlight.js pack). */
:root, [data-theme="github-dark"] {
  --bg:#0d1117;--fg:#e6edf3;--heading:#e6edf3;--link:#2f81f7;
  --code-bg:#161b22;--border:#30363d;--muted:#8b949e;
  --menu-bg:#161b22;--menu-border:#30363d;--menu-hover:#21262d;--menu-fg:#e6edf3;
}
[data-theme="github"] {
  --bg:#ffffff;--fg:#1f2328;--heading:#1f2328;--link:#0969da;
  --code-bg:#f6f8fa;--border:#d0d7de;--muted:#656d76;
  --menu-bg:#ffffff;--menu-border:#d0d7de;--menu-hover:#f6f8fa;--menu-fg:#1f2328;
}
[data-theme="dracula"] {
  --bg:#282a36;--fg:#f8f8f2;--heading:#bd93f9;--link:#8be9fd;
  --code-bg:#21222c;--border:#44475a;--muted:#6272a4;
  --menu-bg:#21222c;--menu-border:#44475a;--menu-hover:#44475a;--menu-fg:#f8f8f2;
}
[data-theme="monokai"] {
  --bg:#272822;--fg:#f8f8f2;--heading:#a6e22e;--link:#66d9ef;
  --code-bg:#1e1f1c;--border:#49483e;--muted:#75715e;
  --menu-bg:#1e1f1c;--menu-border:#49483e;--menu-hover:#3e3d32;--menu-fg:#f8f8f2;
}
[data-theme="nord"] {
  --bg:#2e3440;--fg:#d8dee9;--heading:#88c0d0;--link:#81a1c1;
  --code-bg:#3b4252;--border:#4c566a;--muted:#616e88;
  --menu-bg:#3b4252;--menu-border:#4c566a;--menu-hover:#434c5e;--menu-fg:#eceff4;
}
[data-theme="atom-one-dark"] {
  --bg:#282c34;--fg:#abb2bf;--heading:#e06c75;--link:#61afef;
  --code-bg:#21252b;--border:#3e4451;--muted:#5c6370;
  --menu-bg:#21252b;--menu-border:#3e4451;--menu-hover:#2c313a;--menu-fg:#abb2bf;
}
[data-theme="solarized-dark"] {
  --bg:#002b36;--fg:#839496;--heading:#268bd2;--link:#2aa198;
  --code-bg:#073642;--border:#586e75;--muted:#657b83;
  --menu-bg:#073642;--menu-border:#586e75;--menu-hover:#094352;--menu-fg:#93a1a1;
}
[data-theme="vs2015"] {
  --bg:#1e1e1e;--fg:#d4d4d4;--heading:#569cd6;--link:#4ec9b0;
  --code-bg:#252526;--border:#3c3c3c;--muted:#808080;
  --menu-bg:#252526;--menu-border:#3c3c3c;--menu-hover:#2a2d2e;--menu-fg:#cccccc;
}
*{box-sizing:border-box;margin:0;padding:0}
html,body{height:100%}
body{
  background:var(--bg);color:var(--fg);
  font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
  font-size:15px;line-height:1.7;
  user-select:none;
}
#page{max-width:956px;margin:0 auto;padding:48px 48px 64px}
#content,#content *,input,textarea{
  user-select:text;
}
#titlebar{
  position:fixed;top:0;left:0;right:0;height:32px;
  z-index:180;display:flex;align-items:center;padding:0 12px;
  background:transparent;color:var(--muted);font-size:11px;letter-spacing:.03em;
  cursor:move;user-select:none;
  transition:background .15s ease;
}
#titlebar:hover{
  background:var(--menu-bg);border-bottom:1px solid var(--border);
}
#titlebar .tb-label{opacity:0;transition:opacity .15s ease;pointer-events:none}
#titlebar:hover .tb-label{opacity:.75}
#controls{
  position:fixed;top:4px;right:10px;display:flex;gap:4px;
  opacity:0;transition:opacity .2s;z-index:200;
}
body:hover #controls{opacity:1}

#version{
  position:fixed;bottom:6px;left:10px;font-size:10px;color:var(--muted);
  opacity:0;transition:opacity .2s;z-index:150;
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
  padding:5px 9px;transition:background .15s;
}
.ctrl-btn:hover{background:rgba(128,128,128,.35)}
#ctx-menu{
  position:fixed;background:var(--menu-bg);border:1px solid var(--menu-border);
  border-radius:8px;box-shadow:0 8px 28px rgba(0,0,0,.35);
  padding:5px 0;min-width:190px;z-index:1000;
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
  user-select:text;
}
pre{
  background:var(--code-bg);border-radius:8px;margin:1em 0;
  overflow-x:auto;padding:1em 1.2em;
  user-select:text;
}
pre code{background:none;font-size:.9em;padding:0}
table{border-collapse:collapse;margin:1em 0;width:100%}
th,td{border:1px solid var(--border);padding:.5em .9em;text-align:left}
th{background:var(--code-bg);font-weight:600}
tr:nth-child(even) td{background:rgba(128,128,128,.05)}
img{max-width:100%;border-radius:4px;border:1px solid var(--border)}
hr{border:none;border-top:1px solid var(--border);margin:1.5em 0}
input[type="checkbox"]{margin-right:.4em}
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
<div id="titlebar" title="Drag to move window"><span class="tb-label">mdviewer</span></div>
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
const HLJS_CSS = __HLJS_JSON__;
const THEME_LIST = __THEMES_LIST_JSON__;

let currentTheme = '__THEME__';

const hljsStyle = document.getElementById('hljs-theme');
const ctxMenu   = document.getElementById('ctx-menu');

function setTheme(key) {
  if (!HLJS_CSS[key] && !THEME_LIST.some(([k]) => k === key)) return;
  currentTheme = key;
  document.body.dataset.theme = key;
  hljsStyle.textContent = HLJS_CSS[key] || '';
  ctxMenu.querySelectorAll('.theme-item').forEach(el => {
    el.textContent = (el.dataset.key === key ? '\\u2713  ' : '    ') + el.dataset.label;
    el.classList.toggle('active', el.dataset.key === key);
  });
  persistSettings();
}

function persistSettings() {
  if (window.pywebview && window.pywebview.api && window.pywebview.api.save_config) {
    pywebview.api.save_config({theme: currentTheme});
  }
}

async function buildMenu(x, y) {
  ctxMenu.replaceChildren();

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
  lbl.textContent = 'Theme';
  ctxMenu.appendChild(lbl);

  THEME_LIST.forEach(([key, label]) => {
    const item = document.createElement('div');
    item.className = 'ctx-item theme-item';
    item.dataset.key   = key;
    item.dataset.label = label;
    item.textContent   = (key === currentTheme ? '\\u2713  ' : '    ') + label;
    if (key === currentTheme) item.classList.add('active');
    item.onclick = () => { setTheme(key); closeMenu(); };
    ctxMenu.appendChild(item);
  });

  positionMenu(x, y);
}

function positionMenu(x, y) {
  ctxMenu.hidden = false;
  const mw = ctxMenu.offsetWidth, mh = ctxMenu.offsetHeight;
  ctxMenu.style.left = Math.min(x, window.innerWidth  - mw - 8) + 'px';
  ctxMenu.style.top  = Math.min(y, window.innerHeight - mh - 8) + 'px';
}

function copyTextFallback(text) {
  const ta = document.createElement('textarea');
  ta.value = text;
  ta.style.cssText = 'position:fixed;left:-9999px;top:0';
  document.body.appendChild(ta);
  ta.focus();
  ta.select();
  document.execCommand('copy');
  ta.remove();
}

async function copyText(text) {
  if (!text) return;
  try {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      await navigator.clipboard.writeText(text);
    } else {
      copyTextFallback(text);
    }
  } catch (_) {
    copyTextFallback(text);
  }
}

function buildCopyMenu(text, x, y) {
  ctxMenu.replaceChildren();
  const item = document.createElement('div');
  item.className = 'ctx-item';
  item.textContent = 'Copy';
  item.onclick = async () => { await copyText(text); closeMenu(); };
  ctxMenu.appendChild(item);
  positionMenu(x, y);
}

function closeMenu() { ctxMenu.hidden = true; }

document.addEventListener('contextmenu', e => {
  const target = e.target instanceof Element ? e.target : e.target.parentElement;
  const selection = window.getSelection ? window.getSelection().toString() : '';
  e.preventDefault();
  if (selection && target && target.closest('#content')) {
    buildCopyMenu(selection, e.clientX, e.clientY);
    return;
  }
  buildMenu(e.clientX, e.clientY);
});
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

// Window movement: use Win32's native caption-drag loop, not pywebview easy_drag.
// The WM_NCLBUTTONDOWN(HTCAPTION) trick is ignored by this frameless
// WinForms/WebView2 window, and pywebview's easy_drag passes deltas into an
// absolute move (the known "jump" bug). So we trigger a Python-side poll loop
// that follows the cursor in physical pixels via SetWindowPos.
function startNativeDrag() {
  jslog('startNativeDrag: pywebview=' + !!(window.pywebview && window.pywebview.api) +
        ' hasCustomDrag=' + !!(window.pywebview && window.pywebview.api && window.pywebview.api.custom_drag_begin));
  if (window.pywebview && window.pywebview.api && window.pywebview.api.custom_drag_begin) {
    pywebview.api.custom_drag_begin();
  }
}

const titlebar = document.getElementById('titlebar');
if (titlebar) {
  titlebar.addEventListener('mousedown', e => {
    jslog('titlebar mousedown button=' + e.button);
    if (e.button !== 0) return;   // left button only
    e.preventDefault();
    startNativeDrag();
  });
  titlebar.addEventListener('mouseup', () => {
    if (window.pywebview && window.pywebview.api && window.pywebview.api.custom_drag_end) {
      pywebview.api.custom_drag_end();
    }
  });
}
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
        .replace('__HLJS_JSON__',      hljs_json)
        .replace('__THEMES_LIST_JSON__', themes_list_json)
        .replace('__THEME__',        init_theme)
        .replace('__VERSION__',      version)
    )
