<div align="center">
    <img src="./src/icon.png" width="200" height="200">
</div>


Zotcott
=======
First - an -enormous- thank you to Deanishe and @GiovanniCoppola for years of supporting an Alfred/Zotero workflow that I don't believe either of them used for very long.

All of the code changes are AI, so if that's a deal breaker for you, know this upfront.

Also, the workflow now requires node. I used brew to install node.js, but those sorts of dependencies may not be appropriate to Alfred, so it's not gallery ready/free of additional user work.

Zothero had become slow in copying/pasting citations, and was originally built against very old versions of Zotero, which has changed quite a bit in the last few releases. As I do not use BetterBibTex, I have disabled that portion of the work flow.

Zotcott is a fork designed to speedup citation copy/paste and resolve longstanding legacy bugs in an Alfred workflow to access a Zotero database. 

Just in case anybody might find this useful, and again, with deep thanks to those who have kept versions of this tool alive for many years, I've made it available here.

=========
Begin AI generated description:


Local performance fork of [ZotHero][zothero] — an [Alfred][alfred] workflow for rapidly searching your Zotero database and copying citations.

ZotHero is by Dean Jackson ([@deanishe](https://github.com/deanishe)), currently maintained by Giovanni Coppola ([@giovannicoppola](https://github.com/giovannicoppola)). Zotcott is a public fork with no upstream ambitions; it installs alongside a live ZotHero without touching it (separate bundle ID, separate keywords, separate caches).

<!-- MarkdownTOC autolink="true" bracket="round" depth="3" autoanchor="true" -->

- [What's different from ZotHero](#whats-different-from-zothero)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
    - [Pasting citations](#pasting-citations)
- [Configuration](#configuration)
    - [Zotero data](#zotero-data)
    - [Citation styles](#citation-styles)
    - [Locales](#locales)
    - [All settings](#all-settings)
- [Development notes](#development-notes)
- [Licence & thanks](#licence--thanks)
- [Changelog](#changelog)

<!-- /MarkdownTOC -->


<a name="whats-different-from-zothero"></a>
What's different from ZotHero
-----------------------------

Forked from the ZotHero 2.4 release asset (the v2.3.1/v2.4 git tags point at a stale 2023 commit; the real 2.4 source exists only inside the `.alfredworkflow` release assets, archived in `releases/`).

**Performance** — copying a citation took ~4.5–6s in ZotHero 2.4; Zotcott does it in well under a second:

- **Node citation backend** (`src/lib/cite/cite-node.js`). ZotHero generates citations by running a citeproc-js bundle under JXA (`osascript -l JavaScript`), which costs ~3s per run in Apple JS runtime overhead alone. Zotcott runs the same engine under Node. The JXA program is retained as a fallback when Node is missing, but still embeds the old engine (see below) — Node is the supported backend.
- **No database sync on the citation path.** ZotHero re-copied its cached `zotero.sqlite` (541MB on the development library) whenever the live database's mtime was newer — nearly always while Zotero is running, adding ~1.5s per copy. Zotcott reads the cited entry from the search index directly and falls back to a full sync only when the entry is missing. The search path keeps its existing freshness machinery unchanged.

**Correctness** — two related fixes (2.4.1):

- **citeproc-js upgraded to 1.4.61.** The engine ZotHero bundles predates CSL 1.0.2 and does not know `page-range-format="chicago-16"`, which the current Chicago styles (17th and 18th ed.) declare. Citing any entry **with a page range** in those styles crashed the engine (`page_mangler is not a function`).
- **Silent APA fallback removed.** Upstream masked that crash by quietly re-citing in APA (then MLA, Chicago author-date, IEEE) and reporting success — so Chicago citations of paged entries came back as APA with no visible warning. Citation errors now surface as errors.

**Identity** — bundle ID `zotcott`, keywords `zcot` / `zcot:` / `zcotconf` (search / field search / config), default style Chicago Manual of Style 18th edition (notes and bibliography). Alfred keys data and cache directories by bundle ID, so Zotcott and a live ZotHero coexist without interference.


<a name="requirements"></a>
Requirements
------------

- Alfred 5 (Powerpack)
- Zotero 5+ with locally installed styles
- **Node** (`brew install node`). Alfred's minimal `PATH` omits Homebrew, so the workflow checks `PATH` and the standard Homebrew locations; set `ZOTCOTT_NODE` in the workflow configuration to point at a non-standard install. Without Node the workflow falls back to the slow JXA citation program, which still has the pre-1.0.2 CSL engine and will fail on modern Chicago styles.


<a name="installation"></a>
Installation
------------

Double-click `releases/Zotcott-<version>.alfredworkflow` (built by zipping the contents of `src/`):

```
cd src && zip -r ../releases/Zotcott-X.Y.Z.alfredworkflow . -x '*__pycache__*' -x '*.pyc'
```


<a name="usage"></a>
Usage
-----

- `zcot <query>` — Search your Zotero database (common fields).
    - `↩` — Open the entry in Zotero. (`fn+↩` is an alternate)
    - `⌘↩` — Copy citation to the pasteboard (see [Configuration](#configuration)).
    - `⌥↩` — Copy bibliography-style citation to the pasteboard (see [Configuration](#configuration)).
    - `⇧↩` — View entry attachments (if present).
        - `↩` — Open an attachment in the default application.
        - A linked file that isn't on disk (an orphaned path from another machine, or a cloud file that isn't synced) is shown as a non-actionable "⚠ File not found" item instead of failing silently on open.
    - `^↩` — View all citation styles.
        - `↩` or `⌘↩` — Copy citation in selected style.
        - `⌥↩` — Copy bibliography-style citation in selected style.
        - `^↩` — Set style as default.

- `zcot:[<query>]` — Search a specific field.
    - `↩` — Select a field to search against.
- `zcotconf [<query>]` — View and edit workflow configuration.
    - `Default Style: …` — Choose a citation style for the `⌘↩` and `⌥↩` hotkeys (on search results).
    - `Locale: …` — Choose a locale for the formatting of citations. If unset, the default for the style is used, or if none is set, US English.
    - `Reload Zotero Cache` — Clear the workflow's cache of Zotero data. Useful if the workflow gets out of sync with Zotero.
    - `Open Log File` — Open the workflow's log file. Useful for checking on indexing problems (the indexer output isn't visible in Alfred's debugger).

The snippet trigger present in ZotHero was removed from this fork.


<a name="pasting-citations"></a>
### Pasting citations ###

When you copy a citation, Zotcott puts an HTML representation on the pasteboard, suitable for pasting into text/Markdown documents.


<a name="configuration"></a>
Configuration
-------------

The workflow reads Zotero's own config files and partly manages its own configuration with the keyword `zcotconf`, but you may need to use the [workflow configuration sheet][conf-sheet] if the workflow can't read Zotero's config files.

**NOTE:** Unlike its main database, Zotero does not save changes to its configuration until the application closes. As such, if you change Zotero's data or attachment directories, the workflow won't see the changes until you quit Zotero.


<a name="zotero-data"></a>
### Zotero data ###

The workflow uses your Zotero database and styles, therefore it needs to know where to find them. The workflow tries to read Zotero's own configuration files, and falls back to `~/Zotero` (the default location for Zotero 5).

If the workflow can't find your data, you need to set `ZOTERO_DIR` in the [workflow configuration sheet][conf-sheet].

Similarly, if you have set a "Linked Attachment Base Directory" in Zotero, but the workflow can't find the directory, enter its path for `ATTACHMENTS_DIR` in the [configuration sheet][conf-sheet].

**Note**: You can use the UNIX shortcut `~` to represent your home directory, e.g. `~/Zotero` for Zotero 5's default directory.


<a name="citation-styles"></a>
### Citation styles ###

The workflow uses the CSL styles you have installed in Zotero, so to add a new style, simply add it in Zotero. The workflow will pick up the new style(s) on the next run.

You can copy either a citation-/note-style citation or a bibliography-style one by hitting `⌘↩` or `⌥↩` respectively on a search result or citation style.

For `⌘↩` and `⌥↩` to work on search results, you must first choose a default style. You can either do this in the configuration screen (keyword `zcotconf`), or hitting `^↩` on a search result to show all citation styles, then `^↩` on a style to set that as the default.


<a name="locales"></a>
### Locales ###

The default behaviour is to use the locale specified in the style if there is one, and `en-US` (American English) if not. Setting a locale overrides the style's own locale. Use the `zcotconf` keyword to force a specific locale; the bundled locale files are in `src/lib/cite/locales/` (the standard CSL locale set, 50+ languages).


<a name="all-settings"></a>
### All settings ###

These are all settings available in the [workflow configuration sheet][conf-sheet].

You probably shouldn't edit the `CITE_STYLE` or `LOCALE` variables yourself, as there's no guarantee the value you set is actually available. Adjust them using the `zcotconf` keyword.

|      Variable      |                                 Meaning                                 |
|--------------------|-------------------------------------------------------------------------|
| `mainkeyword`      | Search keyword. Default: `zcot` (field search is `<keyword>:`).         |
| `ATTACHMENTS_DIR`  | Path to your Zotero attachments. Read from Zotero's config by default.  |
| `CITE_STYLE`       | Citation style copied by `⌘↩` and `⌥↩`. Default: Chicago 18 (notes and bibliography). |
| `LOCALE`           | Locale for citations. Default: `en-US` (US English).                    |
| `ZOTERO_DIR`       | Path to your Zotero data. Read from Zotero's config by default.         |
| `ZOTCOTT_NODE`     | Path to the `node` executable, if not on `PATH` or in a standard Homebrew location. |


<a name="development-notes"></a>
Development notes
-----------------

- Source of truth is `src/` on the `zotcott` branch; the installed workflow (Alfred prefs, bundle ID `zotcott`) is deployed by copying changed files or reinstalling the release artifact. If you edit the workflow in Alfred's UI, port the change back to `src/` so they agree.
- `src/lib/cite/citeproc-bundle.js` is upstream `citeproc.js` (Juris-M, 1.4.61) verbatim plus a marked CommonJS export footer at the bottom — re-apply the footer if you upgrade the bundle.
- The JXA fallback (`src/lib/cite/cite`) still embeds the old pre-CSL-1.0.2 engine. It is exercised only when Node is missing, and will error (visibly) on styles declaring `page-range-format="chicago-16"`. Upgrading or removing it is an open question.
- `experiments/` is an untracked sandbox; `experiments/repro-page-mangler.js` is a minimal reproduction of the page-range engine crash, useful for testing future engine upgrades (run it against any bundle and the four `page-range-format` values).
- **No self-updater.** The bundled Deanishe Alfred-Workflow auto-updater (`lib/workflow/update.py` and the `update_settings` hooks in `workflow.py`) was removed deliberately on 2026-06-15; distribution is manual — rebuild the `.alfredworkflow` zip and `open` it per machine. The only distribution follow-up still under consideration is possibly submitting to the [Alfred gallery][gallery], which would require resolving the Node dependency (see Requirements) before the workflow is gallery-ready.


<a name="licence--thanks"></a>
Licence & thanks
----------------

This workflow is released under the [MIT licence][licence].

It is heavily based on [Alfred-Workflow][aw] (also MIT) for the workflow stuff, and [citeproc-js][citeproc-js] v1.4.61 ([AGPL][citeproc-licence]) for generating the citations.

ZotHero was inspired by the now-defunct [ZotQuery][zotquery] by [@fractaledmind][smargh]. The [Zorro icon][icon-source] was created by [Dan Lowenstein][lowenstein] from [the Noun Project][noun-project].


<a name="changelog"></a>
Changelog
----------------

- 2026-06-15 **Zotcott 3.2.0**: modernisation pass for Zotero 8/9 (current library is Zotero 9.0.4, schema 125).
    - **Hardened attachment resolution.** Profile detection in `config.py` now resolves the active Zotero profile across all `profiles.ini` layouts (an `[Install…]` `Default=` path, a profile flagged `Default=1`, a profile named `default`, or the sole profile) instead of only matching `Name=default` — the old single-line failure mode silently dropped *every* linked attachment. Linked files missing from disk are now surfaced as "⚠ File not found" rather than failing silently on open (`Attachment.exists`).
    - **Removed the Better BibTeX / citekey subsystem.** Deleted `betterbibtex.py`, the `do_citekey` command, the `COPY_CITEKEY_MOD` search-result branch, and the per-load citekey lookup. The cite-in-place / autopaste path is untouched. (The Alfred-side "Copy Citekey" objects and the `COPY_CITEKEY_MOD` config variable are now inert; remove them via the Alfred workflow editor if desired.)
    - **Search index migrated FTS3 → FTS5.** Ranking now uses SQLite's built-in `bm25()` with per-column weights, replacing the hand-rolled `matchinfo`/`struct` rank function. The index schema version bumped (8 → 9), so the search cache rebuilds itself on first run.
    - Added a pytest suite (`src/lib/zothero/tests/`: config, models, zotero, index) covering the above.
    - **Fixed three Python 3.14 bugs in `util.py`:** `asciify()` returned raw bytes (mangling cached style filenames via `safename()`); `strip_tags()` returned an object repr instead of text (garbling note text in the index — `HTMLText` lacked `__str__`); and `parse_date()` truncated non-date strings to four characters. Revived `test_util.py`; the suite is 22/22 green.
- 2026-06-15 **Zotcott 3.1.0**: rich-text copy. Citations now land on the clipboard with a styled **RTF** flavor *and* a plain-text flavor, so rich-text targets (Word, Pages, Mail, Notes) get real italics while plain-text targets (BBEdit, Terminal) get clean, tag-free text. Previously `do_copy` copied `data['text']` — which is HTML — so italics pasted as literal `<i>…</i>` tags. The styled `rtf` form was already generated on every copy and discarded. Implemented via JXA (`osascript -l JavaScript` → `NSPasteboard`) fed the RTF over stdin, with the plain-text flavor derived from the RTF itself via `NSAttributedString`; no new dependency (the workflow's Homebrew python3 has no PyObjC, but `osascript` ships with macOS). Falls back to plain `pbcopy` if the rich path ever fails.
- 2026-06-15 **Zotcott 3.0.0**: version-line break — no functional change from 2.4.1. Renumbered to a major Zotcott line so the fork's versions can never collide with upstream ZotHero's (both had reached "2.4"). Inherited `ZotHero*.alfredworkflow` artifacts removed from `releases/`; only `Zotcott-*` builds are kept. Upstream ZotHero releases remain on [GitHub][zothero-releases] if ever needed.
- 2026-06-12 **Zotcott 2.4.1**: citeproc-js upgraded to 1.4.61 — fixes engine crash (`page_mangler`) on entries with page ranges in modern Chicago styles, which upstream had masked by silently substituting APA; the silent fallback is removed and citation errors now surface.
- 2026-06-12 **Zotcott 2.4**: forked from the ZotHero 2.4 release asset. Node citation backend (~4× faster than JXA); citation path no longer re-copies the Zotero database (~0.7s vs ~4.5–6s per copy overall); bundle ID `zotcott`, keywords `zcot`/`zcot:`/`zcotconf`; default style Chicago 18 (notes and bibliography); snippet trigger removed.
- Upstream history: see [ZotHero releases][zothero-releases] (2.2: newer BetterBibtex support; 2.1; 2.0: Alfred 5).

[alfred]: https://www.alfredapp.com/
[aw]: http://www.deanishe.net/alfred-workflow/
[citeproc-licence]: https://github.com/Juris-M/citeproc-js/blob/master/AGPLv3
[citeproc-js]: https://github.com/Juris-M/citeproc-js
[conf-sheet]: https://www.alfredapp.com/help/workflows/advanced/variables/#environment
[csl]: http://citationstyles.org
[gallery]: https://alfred.app/
[icon-source]: https://thenounproject.com/term/zorro/14540/
[licence]: ./LICENCE
[lowenstein]: https://thenounproject.com/danny_mustache
[noun-project]: https://thenounproject.com
[smargh]: https://github.com/fractaledmind
[zotquery]: https://github.com/fractaledmind/alfred_zotquery
[zothero]: https://github.com/giovannicoppola/zothero
[zothero-releases]: https://github.com/giovannicoppola/zothero/releases
