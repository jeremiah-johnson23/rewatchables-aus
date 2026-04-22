# Rewatchables AU (Streaming Guide)

Before starting any work, read these files from the simon-context repo (`~/simon-context/`):

1. **BRIEF.md** - Voice, tone, and working preferences
2. **PROJECTS.md** - Active project status and priorities
3. **DECISIONS.md** - Settled decisions (do not relitigate)

## Repo Context

Australian streaming guide for The Rewatchables podcast. Shipped and live at rewatchables.au. Lower priority "building" project (P9).

Vanilla JS + Tailwind, hosted on GitHub Pages. Weekly auto-update workflow checks for new episodes via RSS. Monthly streaming audit needed for licensed content (144 movies rotate between services).

This project is shipped and mostly in maintenance mode. Focus on keeping data accurate and the auto-update pipeline healthy.

## Session Memory

### Session 10 — 2026-04-22
- **Diagnosed TMDB root cause:** Every CI run since Session 8 (Mar 25) returned HTTP 401 from TMDB on the first request. Episodes only got populated because Mr Bookman ran enrichment locally after each failure — the CI auto-enrichment has literally never worked
- **Likely cause:** wrong credential type in `TMDB_API_KEY` secret (v4 Read Access Token pasted into v3-style `?api_key=` path)
- **Fix path not taken:** patched the script for v3/v4 auto-detection (kept in git history); Mr Bookman declined the TMDB application form, so we switched source entirely
- **Switched to Wikidata:** no API key, no signup, CC0. Pipeline: Wikipedia search (`?gsrsearch={title} film`) → Wikidata SPARQL for year, director, genres, production company (P272), distributor (P750)
- **Studio field choice:** prefer P750 distributor over P272 production — P272 commonly names the producer (Imagine Entertainment for Kindergarten Cop, PolyGram for Fargo, Starz for Sicario) rather than the recognised studio. STUDIO_MAP naturally filters out secondary distributors like Netflix/Microsoft Store
- **Genre cap:** Wikidata returns 5–13 overlapping genres per film; split on spaces, strip "film" suffix, match per-token, cap at 4 by priority (Drama/Comedy/Action/Crime/Thriller first)
- **Filled Kindergarten Cop (1990):** Ivan Reitman, Universal, Comedy/Action/Thriller, Binge + rentals
- **Workflow cleaned:** removed `TMDB_API_KEY` env var, renamed step, updated email copy. Live smoke test via `workflow_dispatch` passed (8s, green)
- **Unresolved:** Eddie and the Cruisers (Apr 7) streaming=all-false unconfirmed; unused `TMDB_API_KEY` secret still in repo settings; Node 20 actions deprecation (forced June 2026)
- Gordo Framework v0.8.0, Session 3

### Session 9 — 2026-04-01
- **Diagnosed auto-update partial failure:** L.A. Confidential (Mar 31) skeleton added with streaming + podcast URLs, but TMDB enrichment failed silently (year, director, genres, studio all empty)
- **Root cause:** `enrich_metadata.py` returned 0 even on failure, so workflow looked green
- **Filled out L.A. Confidential (1997):** Curtis Hanson, Warner Bros, Crime/Drama/Mystery/Thriller, Stan + Disney+
- **Fixed TMDB failure visibility:** Script now exits non-zero on enrichment failure; workflow uses `continue-on-error` so streaming/podcast steps still run
- **Added weekly email notifications via Resend:** Success (green), partial failure (warning), or no-op (info) sent to simon@reflive.com after every workflow run
- **RESEND_API_KEY** added as GitHub repo secret
- Gordo Framework v0.8.0, Session 2

### Session 8 — 2026-03-25
- **Filled out The Nice Guys (2016)** skeleton: Shane Black, Warner Bros, Action/Comedy/Crime, Stan (AU), episode-specific Spotify + Apple Podcast URLs
- **Built auto-enrichment pipeline:** New `scripts/enrich_metadata.py` uses TMDB API to fill year, director, genres, studio on skeleton entries
- **Upgraded weekly workflow:** `check-new-episodes.yml` now chains: add skeleton → TMDB enrich → JustWatch streaming → Apple Podcast URLs → commit & push
- **TMDB_API_KEY** added as GitHub repo secret
- **4 other episodes already live** from auto-update since Session 7: Sicario (Mar 3), Fargo (Mar 10), To Live and Die in L.A. (Mar 17), plus a mailbag — all fully populated except The Nice Guys
- **Limitation:** Spotify episode URLs still manual (no free API without OAuth)
- Gordo Framework v0.8.0, Session 1

### Session 7 — 2026-02-25
- **Filled out Crazy, Stupid, Love. (2011)** skeleton: Ficarra/Requa, Warner Bros, Comedy/Romance/Drama, Prime Video + HBO Max, episode-specific podcast URLs
- **Fixed GoldenEye streaming error** from Session 6: Prime Video was rent-only in AU, not subscription. Set primeVideo: false, added Google Play to rentBuy
- **Fixed fetch_streaming_availability.py bugs:**
  - Provider ID 1899 was mapped to Stan but is actually HBO Max
  - Added hboMax to parse_offers output dict (was missing)
  - Added Prime Video with Ads (ID 2100) to provider map
- **Lesson:** Always verify streaming via JustWatch FLATRATE vs RENT/BUY distinction. Don't trust web search summaries for AU availability. The script handles this correctly; manual entries are where errors crept in.
- **Full streaming audit:** Ran fetch script with new `--force` flag across all 435 movies. 431 updated via JustWatch, 4 failed lookup.
- **Notable shifts:** HBO Max 17→40 (provider ID fix), Stan 150→121, Prime Video 61→47, Disney+ 80→84, Paramount+ 43→46
- **Chased down 4 failed lookups:** All had bad metadata from RSS auto-update
  - Sinners: year was 1986, actually 2025 (Ryan Coogler). HBO Max.
  - It: year was 1990 (TV movie), actually 2017 (Muschietti). Netflix/Stan/HBO Max.
  - Mr. Holland: title truncated, year 1993. Fixed to Mr. Holland's Opus (1995). Not streaming in AU.
  - The Sure Thing (1985): not on JustWatch AU. Added director (Reiner) and studio (Universal).
- **Data quality note:** RSS parser produces bad years and truncated titles on some older entries. Worth watching on future skeleton entries.
- 1 new episode since Session 6: Crazy, Stupid, Love (Feb 24)

### Session 6 — 2026-02-18
- **Added GoldenEye (1995)** with full metadata: Martin Campbell, MGM, Stan + Prime Video, Action/Adventure/Thriller
- **Resolved merge conflict** with auto-update: remote had added skeleton entries for GoldenEye, Ace Ventura: Pet Detective, and Wild Things since last session
- Auto-update quality improving — Ace Ventura entry came in fully populated (director, year, genres, streaming, studio, podcast URLs)
- **3 new episodes since Session 5:** Wild Things (Feb 3), Ace Ventura (Feb 10), GoldenEye (Feb 17)
- Gordo Framework v0.8.0
