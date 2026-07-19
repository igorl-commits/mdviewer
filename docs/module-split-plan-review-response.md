# Response to review: module-split plan & tickets

**Date:** 2026-07-19
**Re:** `docs/module-split-plan-review.md`
**Method:** Every concrete claim re-checked against `mdviewer.py`, `tests/test_config.py`, and the live GitHub issue bodies (#1–#7) before responding.
**Decision:** Adopting re-export strategy **A** (no re-exports; each extract updates its own tests immediately). One branch, six commits.

---

## Summary

The review's factual claims hold. I verified each against the code and the issue bodies rather than taking them on trust, and found no false positives among the high-severity items. Two adjustments below: one finding the review **under-weighted** (ticket #4 asserts something false), and two where I'd **recalibrate the reasoning or severity** (clamp rationale, byte-identical HTML).

---

## Confirmed against source

| Review claim | Evidence |
|---|---|
| #4 omits reading constants + Win32 style constants | Constants live at `mdviewer.py:226-230` (`_GWL_STYLE`/`_GWL_EXSTYLE`/`_WS_THICKFRAME`/`_SWP_FRAMECHANGED`) and `:282-288` (`_PAGE_*`/`_TARGET_READING_CLIENT_LOGICAL`). `_enable_native_resize` (moves to geometry per #4) consumes the style constants; `Api.snap('reading')` consumes `_TARGET_READING_CLIENT_LOGICAL` at `:526`. Neither #4 nor #5 lists them. |
| #3 omits `PRESETS` | `PRESETS` at `:110`, consumed by `build_html`. #3's inventory names `DEFAULTS` but not `PRESETS`. `APP_VERSION` (`:85`) is implied by `_get_version` but not named explicitly. |
| `_dlog`/`_DEBUG` is unowned | Defined once at `:9`/`:23`. Consumed by geometry's `_enable_native_resize` (`:366`), by `Api` throughout (`:383, 387, 391, 395, 447, 472, 478, 486, 502, 556, 562, 581, 593, 604`), and by `main()` (`:1264, 1337`). After the split, three modules import it; no ticket assigns a home. |
| `Api` has undocumented non-callable attrs | `_pre_fullscreen_rect` (`:377`) and `_geom_save_timer` (`:378`) exist on `Api` and are absent from the 4-attr list in both CLAUDE.md and #5. Both already comply with the underscore rule, so the risk is false-confidence in an "inventory," not a live COM-spam bug. |
| Test plan under-specifies mid-flight | `test_config.py` uses `patch('mdviewer.CONFIG_PATH', ...)` in 10 places and `_reload()` reloads `mdviewer` only. Under strategy A these must retarget to `config.*` in the same commit that moves config. |
| #7 docs list incomplete | #7 updates AGENTS.md / CONTEXT.md / adr references but not CLAUDE.md, README.md, tests/AGENTS.md, or docs/agents/domain.md. CLAUDE.md's "All app logic lives in `mdviewer.py`" line plus its key-functions table and asset-bundle/template-location sections would all go stale. |

---

## Under-weighted: ticket #4 asserts something false

The review notes (in a table row) that "#4 never says to update" the geometry tests. The stronger fact: **#4 affirmatively states the opposite.** Its acceptance criteria read:

> "This area has no automated coverage, so manual verification is the only seam."

That is incorrect. `tests/test_config.py` contains automated coverage for geometry code:

- clamp math via `GetSystemMetrics` mocks — `:147-174`
- `_enable_native_resize` via `GetWindowLongW` / `AdjustWindowRectEx` mocks — `:229-233`
- snap math, `_TARGET_READING_*`, and `_geometry_from_window` assertions

An AFK agent executing #4 will read "no coverage," move geometry, skip test updates, and red-bar `pytest` — the exact failure the review warns about, but with the ticket steering into it. **#4's coverage claim must be corrected**, not just supplemented with a test-update step.

---

## Recalibrations

**clamp_position (review §High-2).** Moving it to `geometry.py` is right on cohesion grounds and I'll do it. But the stated rationale — "keeps `config.py` as portable I/O" — doesn't survive contact with #3's own plan: #3 already places `_is_windows_dark_theme` in config, and that reads the Windows registry. Config is Windows-specific regardless of where clamp lands. So this is a tidiness call, not a purity violation; and if config purity is the concern, `_is_windows_dark_theme` is the larger offender, which the review demotes to "medium." Recommend treating both as the same "config is a deliberate grab-bag" decision at one severity.

**"byte-identical HTML" (review §Medium).** Correct that it's false (`APP_VERSION` derives from git count; theme resolves at render). But this is AC wording, not risk. Reword to "same structure, same placeholders filled by the same rules" and move on — it shouldn't inflate scope.

---

## Accepted pre-flight edits

Applying these to the issue bodies before `/implement`:

1. **#4** — add reading constants (`_PAGE_*`, `_SCROLLBAR_GUTTER_LOGICAL`, `_READING_SIDE_MARGIN_LOGICAL`, `_TARGET_READING_CLIENT_LOGICAL`) and Win32 style constants (`_GWL_STYLE`, `_GWL_EXSTYLE`, `_WS_THICKFRAME`, `_SWP_FRAMECHANGED`); add `clamp_position`; **correct the false "no automated coverage" claim** and add the concrete test-update list.
2. **#3** — add `PRESETS`; name `APP_VERSION` ownership explicitly; remove `clamp_position` (now #4).
3. **`_dlog`/`_DEBUG` home** — keep defined in `mdviewer.py`, imported explicitly by `geometry.py`/`api.py`; logging init stays once at entry, guarded. Documented in whichever ticket lands first.
4. **#6** — declare all `build_html` inputs: `assets` constants + `PRESETS` + `_is_windows_dark_theme()` + `APP_VERSION`; soften "byte-identical."
5. **Re-export strategy A** — write "update tests to new import path in this commit; no re-exports" into the test-AC of #3, #4, #5, #6.
6. **Blocking** — chain #3←#2? (no import dep, but same-file serial): state "single branch, serial only" explicitly on #2/#3/#4; drop the misleading "can start immediately."
7. **#7 docs** — expand to CLAUDE.md, README.md, tests/AGENTS.md, docs/agents/domain.md, plus the `py_compile` set for all six files.
8. **#5** — add `_pre_fullscreen_rect`, `_geom_save_timer` to the non-callable-attr list.
9. **#6/#2 ACs** — soften "byte-identical HTML"; make live `fetch_assets.py` fetch a manual smoke check, not a required (network-dependent) AC.
10. **#1** — demote from `ready-for-agent` to tracking map so an implement skill doesn't grab the whole PRD in one shot.

## Not adopting / deferring

- Package layout, new GUI tests, schema changes — agree these are correctly out of scope.
- A dedicated `debug.py` module — overkill for one 2-line helper; explicit import from `mdviewer.py` is simpler (item 3).

---

## Bottom line

Plan direction and boundaries are sound; the gaps are inventory completeness, the test seam, and one false coverage claim in #4. With edits 1–10 applied and strategy A, the split is safe to run serially on one branch.
