# Critical review: module-split plan & tickets

**Date:** 2026-07-19  
**Scope:** Parent #1 + children #2–#7 (post grill-me / to-tickets)  
**Status:** Review only — no implementation started  
**Sources:** GitHub issues #1–#7, `mdviewer.py`, `tests/`, `fetch_assets.py`, DOX docs

---

## Verdict

The direction is sound: pure structural refactor, sensible module seams, migration order that matches the real dependency graph, and no ADR reversals. The parent spec (#1) is stronger than the child tickets.

**Do not start `/implement` yet** without fixing a few concrete gaps. Several will cause broken intermediate states, thrashing, or “agent improvisation” that undoes the pure-move intent.

---

## What holds up

| Decision | Why it’s good |
|----------|----------------|
| Flat modules, not a package | Matches current layout, `sys.path` test trick, and PyInstaller entrypoint |
| Pure move, no renames | Keeps review surface small; matches “no behavior change” |
| Assets / config / geometry first, then api / template, then trim | Real dependency order |
| Underscore rule called out on `Api` | Correct and load-bearing |
| Sentinel comments moved verbatim + `fetch_assets.py` retargeted | Matches CLAUDE.md #6 |
| Theme-cycle markers stay; only the Node file path changes | Correct |
| Out of scope: package layout, new GUI tests, schema changes | Keeps the work bounded |

Problem statement is fair: ~1.3k lines, most of the bulk is the asset blob + HTML string, and AGENTS already treats single-file as accident, not design.

---

## High-severity flaws (fix before implement)

### 1. Incomplete extraction inventories

Tickets list some symbols and omit others that live in the same seams.

**`geometry.py` (#4) is missing:**

- Reading-width constants: `_PAGE_CONTENT_LOGICAL`, `_PAGE_HPAD_LOGICAL`, `_PAGE_MAX_LOGICAL`, `_SCROLLBAR_GUTTER_LOGICAL`, `_READING_SIDE_MARGIN_LOGICAL`, `_TARGET_READING_CLIENT_LOGICAL`
- Win32 style constants: `_GWL_STYLE`, `_GWL_EXSTYLE`, `_WS_THICKFRAME`, `_SWP_FRAMECHANGED`

These are used by `Api.snap('reading')` and `_enable_native_resize`, and **tested via** `mdviewer._TARGET_READING_*`. If they stay in `mdviewer.py` while geometry moves, you get a half-split and broken tests.

**`config.py` (#3) is missing:**

- `PRESETS` (used by `build_html`, defined next to `DEFAULTS`)
- Possibly explicit ownership of `APP_VERSION` (only listed as `_get_version`)

**Orphaned cross-cutting helpers (no ticket owns them):**

- `_DEBUG` / `_dlog` — used by `Api` heavily and by `_enable_native_resize`
- Logging setup at import time

Without an owner, the implementer will either leave them in `mdviewer.py` (and create awkward imports), duplicate them, or invent a sixth module. Decide now: e.g. `debug.py` / keep in `mdviewer.py` and import explicitly / put `_dlog` in a tiny shared place.

### 2. `clamp_position` is miscategorized

Ticket puts it in **`config.py`**. In code it is pure Win32 virtual-screen math (`GetSystemMetrics` SM_*VIRTUALSCREEN). Cohesion says **`geometry.py`**. Tests already treat it as geometry, not config I/O.

Putting it in config forces `config` to import `ctypes`/`windll` and muddies the “config is portable I/O” story. Move it to geometry (or accept a grab-bag `config` and document that consciously).

### 3. Test plan under-specifies the intermediate world

Today almost everything is imported as `mdviewer.X` / `patch('mdviewer.CONFIG_PATH')`, and `_reload()` reloads **`mdviewer` only**.

After moves **without re-exports**:

| Area | Problem |
|------|---------|
| Config tests | Patch target must become `config.CONFIG_PATH`; `_reload()` must reload **`config`**, not only `mdviewer` |
| `Api` + save tests | Still construct `m.Api` while patching config path — after `load_config` lives in `config`, patching `mdviewer.CONFIG_PATH` is a no-op |
| Geometry / reading / snap tests | Still `import mdviewer as m` then `m._find_hwnd`, `m._TARGET_READING_…`, `m._geometry_from_window` — **#4 never says to update these** |
| Source-inspection tests | `inspect.getsource(m.Api.snap)` needs a stable import path after #5 |

**Spec contradiction:** “same public surface, pure move” vs “no re-exports mentioned.” Pick one:

- **A (recommended for serial pure-move):** each extract updates tests to the new module immediately; no re-exports.
- **B:** temporary `from config import …` re-exports in `mdviewer` until #7, then delete re-exports and fix tests once.

Right now tickets imply A for config only and silence for geometry — that will fail green-bar halfway.

### 4. “Blocked by: None” on #2/#3/#4 is operationally wrong

They have **no import dependency**, but they **all edit the same `mdviewer.py`**. Parallel agents / parallel PRs will thrash. On one serial branch, order assets → config → geometry is still required for merge hygiene and an always-runnable tree.

Also: blocking is only prose in issue bodies — **no GitHub native dependencies**, no wayfinder labels. Fine if a human runs `/implement` carefully; bad if automation treats all `ready-for-agent` issues as parallel.

### 5. Docs ticket (#7) is incomplete

It updates `AGENTS.md` but not:

| Doc | Still says single-file / wrong paths |
|-----|--------------------------------------|
| `CLAUDE.md` | “All app logic lives in `mdviewer.py`”, asset bundle section, key-functions table, HTML template location |
| `tests/AGENTS.md` | Patch `mdviewer.CONFIG_PATH`, theme markers in `mdviewer.py` |
| `README.md` | “entire app — single Python file”, fetch_assets patches `mdviewer.py` |
| `CONTEXT.md` | “single-file” opener |
| `docs/agents/domain.md` | tree shows only `mdviewer.py` |
| `AGENTS.md` Purpose line + Verification `py_compile` list | Partially covered |

If docs are part of “done,” expand #7 (or add a docs checklist). Leaving `CLAUDE.md` stale is especially costly — agents will keep editing the wrong file.

### 6. `Api` underscore inventory is incomplete (copied from docs)

#5 (and CLAUDE) list `_window`, `_hwnd`, `_title`, `_md_path`. Live `Api` also has:

- `_pre_fullscreen_rect`
- `_geom_save_timer`

Same rule applies. Incomplete list → false confidence during review.

---

## Medium issues (won’t sink the refactor, will create noise)

### Module cohesion is “where it lived,” not “what it is”

`config.py` as proposed becomes a bag: JSON config, portable path, recent files, encoding helper, version, OS dark-mode, and (wrongly) clamp. Fine for a pure move if stated; bad if sold as deep modules.

Cleaner pure-move map:

| Module | Contents |
|--------|----------|
| `assets.py` | Bundle only |
| `config.py` | `CONFIG_PATH`, `DEFAULTS`, load/save, recent |
| `geometry.py` | Win32 + clamp + reading constants + geometry helpers |
| `theme_os.py` or stay with config | `_is_windows_dark_theme` (only consumer: template) |
| version in config or `mdviewer` | `_get_version` / `APP_VERSION` (only consumer: template) |
| `template.py` | `build_html` + needs `PRESETS`, assets, version, OS theme |
| `api.py` | `Api` |
| shared | `_dlog` / `_DEBUG` |

`PRESETS` belongs with template or config schema — pick one in the ticket text.

### Template dependencies under-declared

`build_html` is not “assets only.” It uses:

- `HLJS_*` / `MARKDOWN_IT_JS` from assets
- `PRESETS`
- `_is_windows_dark_theme()`
- `APP_VERSION`

#6 says “importing from `assets.py`” only. Implementer will rediscover the rest and invent imports. Spell them out.

### Acceptance criteria that overclaim

- **#6 “byte-identical HTML”** — false under `APP_VERSION` (git count) and system theme resolution. Prefer “same structure / same placeholders filled by same rules” or snapshot the pure template with fixed mocks.
- **#2 “re-run `fetch_assets.py` successfully”** — needs network. Prefer offline check: target path is `assets.py`, regex matches sentinels, dry-run or fixture. Optional live fetch as manual smoke.
- **#7 “`mdviewer.py` contains only `main()`”** — true-ish, but `main` also owns file watcher, tk dialogs, event wiring. Wording is fine if “entry + wiring,” not “ten lines.”

### PyInstaller claim is *probably* fine, not proven

Local pure-Python imports next to the entry script are usually collected. Still worth one intermediate `build.bat` after assets+config, not only at the end — asset move is the riskiest packaging change. Ticket only verifies at #7.

### Parent issue also labeled `ready-for-agent`

#1 is the full PRD. An implement skill that grabs any open ready ticket might try to do the whole split in one shot and ignore child AC. Prefer `wayfinder:map` / leave parent unlabeled / close #1 as tracking-only after children exist.

### No explicit “do not change behavior” guardrails in AC

Missing cheap guards agents often break:

- Do not resolve `theme: system` in `load_config`
- Do not cache hwnd in `snap` (fresh `FindWindowW`)
- Do not drop `_enable_native_resize` after fullscreen
- Do not rename asset/theme-cycle sentinels

These are in CLAUDE already; repeating them in #5/#4 AC would reduce regression risk.

### Import-time side effects

`_DEBUG` logging setup runs on import. If every module imports a debug helper that re-inits logging, tests get noisy. Keep init **once** (entry or single debug module with guard).

### `CONFIG_PATH` init trick

```python
if 'CONFIG_PATH' not in globals():
    ...
```

Exists so tests can pre-seed / survive reload. Must move **with** `config.py` and the reload strategy must be documented in the test ticket. Easy to “clean up” and break portable-mode tests.

---

## Process / ticket-quality issues

1. **No real dependency graph in GitHub** — only “Blocked by” text. Serial implement OK; automated parallel not.
2. **No definition of done for the map** — when are all of #2–#7 closed and #1 closed?
3. **No branch/commit strategy** — one branch sequential commits vs six PRs. For this repo size, **one branch, six commits matching tickets** is safer than six merge conflicts on `mdviewer.py`.
4. **Grill outcome under-documented outside #1** — ADRs 0001–0004 are orthogonal (good). No ADR for “flat multi-module layout.” Optional; not required if #1 is the record.
5. **Value proposition is modest** — largest win is `assets.py` + `template.py` (file size / scrape surface). Splitting `api`/`geometry`/`config` helps navigation; it does not unlock features. Still justified by AGENTS debt note — just don’t expect product gains.

---

## Recommended pre-flight edits (cheap, high leverage)

Before `/implement`, update tickets (or a short “implement notes” comment on #1):

1. **Expand #4 symbol list** (reading constants + Win32 style constants + `clamp_position` if you move it).
2. **Expand #3** with `PRESETS` / drop clamp; state `_get_version`/`APP_VERSION`/`_is_windows_dark_theme` ownership.
3. **Own `_dlog`/`_DEBUG`** in one place.
4. **Expand #6 imports**: assets + presets + version + OS dark theme.
5. **Pick re-export strategy** and write it into every extract ticket’s test AC.
6. **Chain blocking**: `#3 blocked by #2` (same-file serial), `#4 blocked by #3`, etc. — or explicitly “single branch, serial only.”
7. **Expand #7 docs list**: CLAUDE.md, README, tests/AGENTS.md, CONTEXT.md, domain tree, py_compile set.
8. **Fix Api attribute list** to include `_pre_fullscreen_rect`, `_geom_save_timer`.
9. **Soften false ACs** (byte-identical HTML; live fetch_assets as required).
10. **Demote #1** from implementable work item to tracking map.

---

## Bottom line

| Layer | Grade |
|-------|--------|
| Goal & scope | Strong |
| Module boundaries (intent) | Good, inventories incomplete |
| Migration order | Correct as dependency order; wrong as “all parallel” |
| Testing strategy | Under-specified mid-flight; will break without re-exports or per-ticket test updates |
| Docs closeout | Incomplete |
| Risk of behavior regression | Low **if** pure move is disciplined; medium if agents “improve” while moving |

**Ship the plan after inventory + test/re-export + docs fixes.** Don’t block on package layout or new GUI tests — those out-of-scope calls are right.

---

## Suggested next steps (when ready)

1. Patch issue bodies (#1–#7) with the fixes above, then `/implement`, or
2. Accept the risks and implement serially on one branch with corrected inventories held only in-session.
