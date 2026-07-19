# Relative markdown images embedded as data URIs

Local images referenced from markdown (e.g. `![…](docs/screenshot.png)`) are
resolved after client-side render by calling `Api.resolve_media`, which joins
the path to the open `.md` file’s directory and returns a `data:` URI.

**Why:** The page is injected as an HTML string (`webview.create_window(html=…)`),
not loaded from a `file://` URL next to the markdown. Relative `img src` therefore
has no filesystem base and shows as broken (seen with the README screenshot).

**Why data URIs (not `file://`):** WebView2 with string-loaded HTML does not
reliably load arbitrary local `file://` resources without extra browser flags.
Embedding keeps the offline, no-extra-deps model.

**Scope:** `http(s):`, `data:`, and `blob:` refs are left unchanged. Missing
files leave the original `src` so the broken-image affordance stays honest.
Drop-loaded content without a disk path cannot resolve relative media.
