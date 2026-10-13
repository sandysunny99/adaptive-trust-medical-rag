# Frontend redesign notes (`ui/3d-redesign`)

Branch `ui/3d-redesign`, created from `chore/claude-code-setup` (8daf010). Not pushed.
Backend code, API contracts, prompts, model routing and the risk classifier are unchanged.

## What changed, in one paragraph

Seven top-level tabs are now three: **Analyze**, **History** and **About**. Analyze opens with a hero and a
3-step "How it works", then the form, then the results. The results now contain the Evidence Trust row,
**Evidence & Sources** and **Security Checks**, which used to be separate tabs. Evaluation and Research Audit
are hidden behind a developer flag. The disclaimer appears twice instead of four times, the model selector
moved into a collapsed "Advanced settings", and the app has a light/dark theme built on design tokens.

## Template choice

There was no 3D template in the repo. Candidates were scored on 2026-10-13 (GitHub API data):

| Candidate | Stars | License | Verdict |
|---|---|---|---|
| magicuidesign/magicui | 22.6k | MIT | **Primary look** (tokens, card glow, particle field) |
| motiondivision/motion | 34.1k | MIT | **Used** for tilt cards and the Magic UI card |
| pmndrs/react-three-fiber + drei | 32.9k / 9.9k | MIT | Not used now: about 250 KB gzip for a minimal scene |
| shadcn-ui/ui | 125.5k | MIT | Token naming reference only |
| DavidHDev/react-bits | 49.1k | MIT + Commons Clause | Rejected (license) |
| tengbao/vanta | 7.2k | MIT | Rejected (no commits since 2024-03) |
| Aceternity UI | n/a | no OSS license | Rejected (license) |

The 3D layer sits behind one lazy boundary, `src/components/hero/ParticleField.tsx`. To try a React Three
Fiber scene later, replace that file's default export; nothing else imports the 3D code.

## Removed, moved, hidden

| Element | Before | After |
|---|---|---|
| Overview tab and its six jargon cards | Top-level tab | Replaced by the hero + "How it works" on Analyze; technical content moved to **About**. `OverviewPage.tsx` deleted (no references left) |
| Evidence tab | Top-level tab, empty until an analysis ran | **Evidence & Sources** section in the results (open by default). `EvidencePage.tsx` kept, now renders the shared `EvidenceList` |
| Security tab | Top-level tab with three PENDING cards | **Security Checks** section in the results (open by default). `SecurityPage.tsx` kept, now renders the shared `SecurityChecks` |
| Evaluation, Research Audit tabs | Always visible, showing only "Failed to load research state." | Hidden unless the dev flag is on; root cause fixed; raw error text replaced with an ErrorState + Retry |
| Disclaimer: Overview amber banner | Shown | Removed |
| Disclaimer: global footer | On every page | Removed; the footer now only links to About |
| Disclaimer: line beside Analyze | Shown | Removed |
| Disclaimer: header badge | "RESEARCH USE ONLY" | Kept; full disclaimer as tooltip and screen-reader text |
| Disclaimer: results | Rendered an **empty** blue box | Kept; falls back to `RESEARCH_DISCLAIMER` when the backend sends none |
| Model selector, "Automatic Failover" badge, router helper text | Always visible | Selector in collapsed **Advanced settings** (default Automatic); badge and auto-mode helper text removed |
| "Verified Evidence (n)" list in results | Frontend-chosen heading; the backend reports `RETRIEVED` | Replaced by Evidence & Sources, showing `provenance_status` as returned |
| Patient Context, Additional Instructions | Plain `<details>` rows | Disclosures with chevron and `aria-expanded` |
| Upload / Enter Drug Names | Underlined tabs | Segmented control (tablist, arrow keys) |
| Analyze button | Looked the same enabled and disabled | Distinct disabled style plus a hint ("Add at least one drug to analyze.") |
| History empty state | Large card plus a separate storage note | One compact row with the note merged in and a "Start an analysis" link |
| Footer floating mid-screen | On short pages | Flex-column layout keeps it at the bottom |
| `src/App.css` | Unused Vite scaffold | Deleted |

## Developer flag

Evaluation and Research Audit show in the nav, and `#evaluation` / `#audit` resolve, only when either:

- the build/dev server has `VITE_SHOW_RESEARCH_TABS=true` (for example in `frontend/.env.local`), or
- the URL has `?debug=1`, e.g. `http://127.0.0.1:5173/?debug=1#audit`.

Without the flag those hashes fall back to `#analyze`.

## Routes

Hash routes: `#analyze` (default), `#history`, `#about`, plus `#evaluation` and `#audit` behind the flag.
Unknown hashes fall back to `#analyze`. Analyze stays mounted behind the `hidden` attribute when another
page is open, so an analysis in progress or finished survives a visit to History or About.

## "Failed to load research state": root cause and production note

`vite.config.ts` proxied only `/api`, `/query` and `/health`. `GET /research-state` therefore hit Vite's SPA
fallback, which returned `index.html` with status 200, and `response.json()` failed with
`Unexpected token '<'`. The backend route itself returned valid JSON. Fix: add `/research-state` to the dev
proxy, and `fetchResearchState()` now rejects non-JSON responses with a clear message.

**Production:** whatever serves the built frontend (reverse proxy, CDN, static host) must forward
`/research-state` to the backend as well, alongside `/api`, `/query` and `/health`.

## Disclaimer root cause (backend follow-up)

`AnalyzeResponse.disclaimer` has a schema default in `src/adaptive_trust_medical_rag/api/live_schemas.py`,
but the live pipeline builds the SSE `answer` payload as a plain dict (`response_data` in
`services/live_application.py`) with no `disclaimer` key, so the default never reaches the client.
`useAnalysis.ts` replaces the whole result with that payload, which is why the box rendered empty. The
frontend now falls back to one constant, `src/constants/disclaimer.ts` (`RESEARCH_DISCLAIMER`, same text
as the schema default), used by the results, the header badge, About and the Markdown export. The backend
fix is described in `../BACKEND_FOLLOWUPS.md`.

## Data shown without frontend computation

- **Evidence Trust row** reads exactly `result.trust.overall_score`, `result.trust.threshold` and
  `result.trust.risk_class`. Numbers are formatted to two decimals, nothing is computed. Missing fields
  show "Not available".
- **Evidence & Sources** lists `result.evidence[]` in backend order with nothing filtered, hidden, reordered
  or relabelled. Each item shows `document_id` and `source_type` as tags, plus `provenance_status`. The
  evidence payload has **no drug/entity field** (keys returned: `chunk_id, document_id, freshness,
  provenance_status, retrieval_method, source_authority, source_name, source_type, text, title,
  trust_score`), so no entity is inferred. The document IDs (for example `SPL-WARFARIN-001`) are what make
  off-target evidence visible.

## Design tokens

All colours live in `src/index.css` as CSS variables and are exposed as Tailwind utilities through
`@theme inline`. Names follow Magic UI's shadcn-style tokens with a clinical teal primary.

| Token | Light | Dark | Use |
|---|---|---|---|
| `--background` | `oklch(0.985 0.004 220)` | `oklch(0.16 0.02 240)` | Page |
| `--foreground` | `oklch(0.18 0.02 240)` | `oklch(0.97 0.005 220)` | Body text |
| `--card` | `oklch(1 0 0)` | `oklch(0.21 0.02 240)` | Solid surfaces: results, trust, warnings |
| `--glass` | `oklch(1 0 0 / 0.6)` | `oklch(0.25 0.02 240 / 0.55)` | Sticky header only |
| `--muted` / `--muted-foreground` | `0.96 …` / `0.47 …` | `0.26 …` / `0.76 …` | Secondary surfaces and text |
| `--border` / `--input` | `0.91 …` / `0.86 …` | 12% / 20% white | Lines, field borders |
| `--primary` / `--ring` | `oklch(0.5 0.1 200)` | `oklch(0.76 0.11 190)` | CTAs, links, focus |
| `--success` / `--warning` / `--destructive` (+ `-soft`) | AA on card and soft backgrounds | lighter variants | ALLOW / FLAG / BLOCK and the disclaimer |
| `--accent-glow`, `--hero-from/to`, `--particle` | | | Hero gradient, CTA glow, particle colour |

- Radius: `--radius: 0.625rem`; sm, md, lg and xl derived from it.
- Fonts: Inter for UI, a monospace stack for IDs and scores.
- Motion: 150 ms hover, 300 ms enter, `cubic-bezier(0.22, 1, 0.36, 1)`. A global
  `prefers-reduced-motion` rule disables animations and transitions.
- Dark mode: a `dark` class on `<html>`. The default follows the system; an explicit choice is stored in
  `localStorage` (`medrag-theme`, wrapped in try/catch), and an inline script in `index.html` applies it
  before first paint.
- 3D: hero particle field (canvas, DPR at most 1.5, about 30 fps, paused when the tab is hidden or the
  hero is off screen, 20% density under 768px, not mounted under reduced motion, where the static radial
  gradient remains). Tilt of ±4° on the three "How it works" cards only. No 3D, glass or animation behind
  results, trust, security or warning content.

## Dependencies added (exact versions)

| Package | Version | License | Why |
|---|---|---|---|
| `motion` | 13.4.3 (peer: React ^18 \|\| ^19) | MIT | TiltCard, Magic UI card |
| `clsx` | 2.1.1 | MIT | `cn()` |
| `tailwind-merge` | 3.7.0 | MIT | `cn()` |

Magic UI code is copied and adapted, not installed. See `THIRD_PARTY_NOTICES.md`.

## Bundle size (production build, gzip)

| | Before (b425dc6) | After |
|---|---|---|
| Initial JS | 84.63 KB | 98.27 KB |
| Initial CSS | 5.27 KB | 6.23 KB |
| Lazy `HowItWorks` chunk (`motion`) | n/a | 42.75 KB |
| Lazy `ParticleField` chunk | n/a | 1.74 KB |

`ParticleField` and `HowItWorks` are separate chunks, loaded after the initial render.

## Lighthouse 12.6.1 (Analyze landing page, `vite preview`, headless Chrome)

| | Performance | Accessibility | LCP |
|---|---|---|---|
| Before, desktop | 100 | 95 | 0.4 s |
| After, desktop | 100 | 100 | 0.5 s |
| Before, mobile | 100 | 95 | 1.5 s |
| After, mobile | 98 | 100 | 2.3 s |

The mobile LCP element is now the hero's intro paragraph (before, it was the footer disclaimer); performance stays at 98.

## Tests

37 tests in 7 files (was 12 in 2). New coverage: Disclosure open/close and `aria-expanded`;
SegmentedControl arrows, Home and End; ErrorState Retry calling the loader again; the dev flag hiding and
showing Evaluation and Audit; hash fallback; the disclaimer fallback when `result.disclaimer` is empty or
missing; trust "Not available"; evidence order and document tags; the Analyze button states; Analyze
staying mounted across pages. The existing model-selector tests now open Advanced settings first, with
their assertions unchanged.

## Screenshots

`docs/redesign/before/` and `docs/redesign/after/` use the same numbering.

| # | Before | After |
|---|---|---|
| 01 | Overview tab | Analyze landing (hero, How it works, form) |
| 02, 03 | Drug names / Upload sub-tabs | Segmented control, collapsed disclosures |
| 04 | History, empty | Compact empty state |
| 05, 06 | Evidence / Security tabs, empty | No longer separate views; see 10 and 11 |
| 07, 08 | Evaluation / Audit: "Failed to load research state." | Real data with `?debug=1`; `08b` shows ErrorState + Retry with the backend stopped |
| 09 | Results | Results with disclaimer, trust row, Evidence & Sources, Security Checks |
| 10, 11 | Evidence / Security tabs, populated | The same content inside the results |
| 12 | n/a | About |
| `dark-*`, `mobile-*` | n/a | Dark mode at desktop width; 375px light and dark |

All inputs are synthetic (Metformin + Amoxicillin; the patient-context run used age 60 and the marker
`SYNTHETIC-CONDITION-TEST`).

## Follow-ups not done

- **JSON export includes patient context** (pre-existing, found during verification). `exportAsJson` nulls
  `patient_context` but the SSE answer payload also carries `patient_context_used`, which is exported as is.
  A one-line fix is ready on request; it was not part of the agreed plan.
- Backend issues in `../BACKEND_FOLLOWUPS.md`: off-target evidence, R0 classification, missing disclaimer.
- Header title truncates to "Adaptive Tr…" at 375px; a short "Medical RAG" title on small screens would read better.
- Unused Vite scaffold assets remain in `src/assets/` (`hero.png`, `react.svg`, `vite.svg`).
- Three pre-existing `react(set-state-in-effect)` lint warnings in `WorkspacePage.tsx` and `HistoryPage.tsx`
  are unchanged; no new warnings were added.
- Existing dependencies in `package.json` still use caret ranges; only the new ones are pinned.
- The full backend test suite was not re-run; nothing outside `frontend/` changed apart from this document's
  sibling `BACKEND_FOLLOWUPS.md`.
