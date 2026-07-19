# Markdown rendered client-side (markdown-it + highlight.js), not server-side in Python

Markdown parsing and syntax highlighting run in the webview via JS
(markdown-it + highlight.js), rather than server-side in Python (e.g.
`python-markdown`/`mistune`) with rendered HTML injected into the page. The
driving reason was wanting highlight.js specifically for syntax
highlighting, which is JS-native — there's no equivalent-quality Python
highlighter that runs in the same process as the renderer.

**Consequence:** the page is a live DOM that Python only ever hands raw
markdown text to (`reloadFromDisk()` + `get_file()`) — live-reload, theme
switching, in-document search, and the image lightbox all operate on that
DOM directly rather than through Python-side HTML regeneration.
