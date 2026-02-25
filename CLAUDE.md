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
