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

### Session 13 — 2026-06-17
- **Pulled 4 auto-added episodes** (catalog 447 → 451): 2001: A Space Odyssey (Jun 1), Animal House (May 26), Single White Female (Jun 8), The Hand That Rocks the Cradle (Jun 15) — all arrived as partial skeletons
- **Fixed 2001: A Space Odyssey year bug:** entry had `year=2001` (parsed from the title, not the film — real year is 1968). Corrected to 1968. Re-fetched streaming with the right year: was `primeVideo` (a wrong-year JustWatch match), actually on **hboMax** + Amazon/Apple TV rent
- **Hand-filled metadata** (Wikidata SPARQL was in an active outage — 429s, 1 req/min, couldn't run `enrich_metadata.py`): 2001 → Kubrick / Sci-Fi,Adventure / mgm; Animal House → Landis / Comedy / universal; The Hand That Rocks the Cradle → studio `disney` (Hollywood Pictures label, absent from STUDIO_MAP so enrich leaves it blank). Re-run enrich later to confirm against Wikidata once it recovers
- **Single White Female:** not actually missing data — already had `rentBuy: Apple TV` (no AU subscription), correctly skipped by the streaming fetch
- **Streaming fetch side effect:** 16 no-AU-offer films (all-false streaming) get re-checked every run since they read as "no streaming data" — their `lastStreamingCheck` bumped to today. Harmless/accurate, same as the weekly workflow
- **Root-caused + fixed the recurring year-from-title bug** (same failure class as Ghostbusters S11, It/Sinners S7): `extract_year_from_description()` in `add_new_episode.py` returned the first 4-digit number in the RSS description. When the title contains one (2001, 2012, 1941), that number won the match — and for 2001 the real year wasn't even in the description. Fix: strip the parsed movie title from the description before scanning, word-boundary matched so short numeric titles (9, 21) don't clobber a digit inside a real year (2009). Title==year films (1984) yield a None hint, which is benign (enrich recovers via Wikipedia search; a wrong hint would mislead it). Verified against the live feed: 2001 → None (was 2001), all other recent episodes unchanged
- **Bumped all GitHub Actions off the deprecated Node 20 runtime** (forced off June 2026): checkout v4→v6, setup-python v5→v6, configure-pages v4→v6, upload-pages-artifact v3→v5, deploy-pages v4→v5. All run on Node 24. Reviewed breaking changes — none affect this repo (dotfile drop irrelevant; configure-pages v5 break is Next-only; setup-python v6 keeps 3.11). Verified live: dispatched both workflows, both green
- **Unresolved (carried from S12):** unused `TMDB_API_KEY` secret still in repo settings; Spotify URLs still show-level; 24 entries with low-confidence Apple URLs awaiting hand-review; Cloudflare Web Analytics beacon pending Simon's token; Wikidata SPARQL outage (transient — re-run enrich on the 3 hand-filled entries once it recovers)

### Session 12 — 2026-05-20
- **Header logo swap:** replaced the Extracting Ideas wordmark with Simon's monogram (`assets/simon-logo.png`) in the "Built by Simon" header
- **Full streaming audit:** ran `fetch_streaming_availability.py --force` across all 447 entries. 446 updated, 1 absent (The Sure Thing 1985, confirmed not on JustWatch AU since Session 7). Catalog grew from 445 → 447 mid-session as the weekly workflow added Tropic Thunder + Borat. Provider shifts: netflix +3, stan -3, primeVideo -7, binge -1, hboMax +1; disney/paramount/appleTv unchanged
- **Apostrophe truncations restored:** pre-Session 11 RSS parser cut 4 titles at the curly apostrophe — St. Elmo → St. Elmo's Fire, Ferris Bueller → Ferris Bueller's Day Off, All the President → All the President's Men, My Best Friend → My Best Friend's Wedding. Year/director already correct; only title and id needed restoring
- **Diagnosed Apple URL matcher silent-sibling bug:** the old `find_best_match` did substring containment (`needle in track_name`) and returned the first hit, so "Rocky" matched "Rocky II With Bill Simmons…" and 11 known entries shipped pointing at the wrong sibling Rewatchables episode (Top Gun → Maverick, Wall Street → Wolf of Wall Street, Friday → Friday Night Lights, Mission: Impossible → Fallout, etc.)
- **Rewrote matcher as scored ranker** in `scripts/fetch_apple_podcast_urls.py:find_best_match`: exact film-name match scores 100/95; prefix + (part N | live | anniversary) extension scores 90; sibling extension 25; substring 15; +50 boost when stored year appears in the track; -70 demote when a different year appears in film_part (catches "Bad Boys 1983" matching a 1995 entry); reject anything < 50. Adds is_live_entry awareness so (Live Show) entries prefer live-variant tracks and non-live entries prefer the regular episode. Splits the " With <hosts>" preamble only at a capital-W followed by a capital first name (preserves "Die Hard With a Vengeance", "Sleeping With the Enemy"). Strips all quote chars in normalize (Apple wraps film names in `'…'` which leaked into film_part). Adds `--force` and `--ids` flags + a year-augmented search retry
- **Backfilled 16 (Live Show) entries:** all now correctly link to their live-variant episodes including the "Re-X LIVE" re-cover pattern (e.g. The Re-Den of Thieves LIVE for the live Den of Thieves entry, Good Will Hunting Live From Boston, Forrest Gump Live From D.C.)
- **Fixed 2 wrong-film metadata entries:** Dec 2023 "National Lampoon" entry was actually Christmas Vacation (1989, Chechik) not regular Vacation — December episode date and Apple URL both confirmed; "The Devil" (2010, Dowdle) had no matching Rewatchables episode and was actually The Devil's Advocate (1997, Hackford) — Apple URL already pointed there but metadata had been mis-mapped by Wikidata enrichment
- **Total Apple URL updates:** 22 in the final catalog-wide --force sweep (after iterative matcher refinement across 3 background runs). 24 entries still flagged "Not found" — keep their existing URLs, need hand-review against the actual podcast feed
- **Multi-part episodes are not duplicates:** flagged 15 (title, year) collisions as duplicates during audit; Simon corrected — they're either re-covers (different host lineups over time, e.g. Jerry Maguire 2017 vs 2024) or multi-part deep dives (Pulp Fiction Part 1+2 on same date). Memory saved at `~/.claude/projects/-home-sjmur/memory/rewatchables_multi_part_episodes.md`
- **Pull-before-push caught divergence:** local was 6 ahead, 2 behind (workflow had auto-added Tropic Thunder + Borat mid-session). Rebase skipped the audit commit and re-ran the audit fresh against the 447-entry catalog to avoid a noisy merge
- **Unresolved:** unused `TMDB_API_KEY` secret still in repo settings (since Session 10); Node 20 actions deprecation (forced June 2026); Spotify URLs still show-level (OAuth limitation); 24 entries with low-confidence Apple URLs awaiting hand-review; Cloudflare Web Analytics beacon pending Simon's token from CF dashboard
- Gordo Framework v0.8.0, Session 5

### Session 11 — 2026-05-05
- **Diagnosed Ghostbusters wrong-film bug:** Apr 28 auto-add filled the entry with the 2016 Paul Feig reboot when the episode was actually about the 1984 Ivan Reitman original. Same RSS-disambiguation failure mode flagged in Session 7
- **Fixed data:** year 1984, Reitman, `sony` studio, streaming Stan + Prime Video FLATRATE per JustWatch AU (the reboot was incorrectly Stan + Binge for this title)
- **Added year-hint pipeline:** `extract_year_from_description()` pulls the year out of the RSS description ("the 1984 comedy classic 'Ghostbusters'"), stored on the skeleton episode. `enrich_metadata.py` now uses the hint to bias the Wikipedia search and validates each candidate's Wikidata pubDate (±1 year), walking up to 5 results before falling back to the top match
- **Verified end-to-end:** with hint=1984, top match is Q108745 (Reitman, sony, Comedy/Action/Horror/Sci-Fi). Without hint, top match was Q20120108 (2016 reboot, Feig)
- **Fixed title parser apostrophe bug:** "There's Something About Mary" was being truncated to "There" because the non-greedy `[^quotes]+` class stopped at the internal `’`. Now strips the " With <hosts>" suffix first, then greedy-matches between outer quotes — the closing curly is unambiguous once hosts are removed. Verified against 7 sample titles + live RSS top 5
- **Race won:** parser fix pushed at 06:48 UTC, cron fires at 07:00 — today's auto-run picks up "There's Something About Mary" cleanly with year_hint=1998
- **Eddie and the Cruisers (1983) resolved:** JustWatch returns the right film with 0 AU offers (no FLATRATE, no rent, no buy). The all-false entry from Session 10 is correct
- **Stale commit-message template:** workflow said "Auto-enriched: TMDB metadata" — updated to "Wikidata metadata" to match current pipeline
- **Unresolved:** unused `TMDB_API_KEY` secret still in repo settings; Node 20 actions deprecation (forced June 2026); Spotify URLs still show-level (OAuth limitation)
- Gordo Framework v0.8.0, Session 4

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
