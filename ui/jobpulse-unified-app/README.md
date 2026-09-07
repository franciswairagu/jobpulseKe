# JobPulse — Unified Frontend

This is the four JobPulse screens (`Dashboard`, `CVAnalyzer`, `JobMarket`, `MarketSkills`)
combined into one app: one navigation shell, one shared state store, and one
data-access layer, instead of four components each holding their own
hardcoded arrays.

**Visual design is untouched.** Same colors, fonts, spacing, card layouts,
and charts as the original files — only the plumbing underneath changed.

## Run it

```bash
npm install
npm run dev      # http://localhost:5173
npm run build    # production build to dist/
```

## What changed, and why

| Before | After |
|---|---|
| Each page had its own hardcoded `skills`/`jobs` arrays | One `src/api/client.js` is the only place that returns this data |
| CV analysis result lived only inside `CVAnalyzer`'s local state | Lives in `src/state/AppContext.jsx`, so the Dashboard and Job Market pages can read it |
| "Match with my CV" button did nothing | Opens a modal that calls `matchJobToCV()`, which needs a real CV analysis to work — and tells the user to go analyze one if they haven't |
| Four separate `<div className="min-h-screen">` shells with duplicated sidebar/header code | One `AppShell` component, one navigation state in `App.jsx` |
| Priorities ("HIGH"/"MEDIUM"/"LOW") were just typed into the array | Computed by `src/lib/scoring.js` from demand/growth/difficulty, so the number is explainable, not invented |

## Project layout

```
src/
  api/
    client.js       <- every function here matches an endpoint in the product spec
                        (getDashboard ~ GET /api/dashboard, analyzeCV ~ POST /api/cv/analyze, etc.)
    mockData.js      <- seed data shaped like the normalized schema (skills, skill_market_stats, jobs)
  lib/
    theme.js         <- single source of truth for colors/fonts (was duplicated 4x before)
    scoring.js       <- transparent skill-priority and CV/job match scoring
  state/
    AppContext.jsx   <- shared app state: profile, cvAnalysis, savedJobs, filters
  hooks/
    useAsync.js      <- loading/success/error wrapper around any api/client.js call
  components/
    layout/AppShell.jsx   <- sidebar + header + mobile nav, ported from Dashboard.jsx
    shared/                <- Dropdown, LoadingState, EmptyState
  pages/
    DashboardPage.jsx, CVAnalyzerPage.jsx, JobMarketPage.jsx, MarketSkillsPage.jsx
  App.jsx            <- which page is active (simple state-based routing, no router needed for 4 screens)
```

## Connecting a real backend later

Every function in `client.js` already has the exact input/output shape the
product spec describes for the real API. To go live, replace the body of
each function with a `fetch()` call — nothing in `pages/` needs to change,
since pages only ever import from `client.js`:

```js
// before (mock)
export async function getJobs({ query, country, remoteOnly }) {
  await delay(350);
  /* ...filter JOBS array... */
}

// after (real backend)
export async function getJobs({ query, country, remoteOnly }) {
  const params = new URLSearchParams({ query, country, remote: remoteOnly });
  const res = await fetch(`/api/jobs?${params}`);
  if (!res.ok) throw new Error("Failed to load jobs");
  return res.json();
}
```

The same is true for `analyzeCV()` (→ `POST /api/cv/analyze`) and
`matchJobToCV()` (→ `POST /api/jobs/:id/match`) — those are the two
functions that should eventually call your AI layer server-side, never from
the browser, so API keys stay off the client.

## What this does *not* include yet

This phase intentionally scoped to the frontend only. Still open, per the
full product spec:

- A real backend/database (`jobPulseke.zip` already has a scraping +
  ingestion + cleaning pipeline with 10,379 real job postings — skill
  extraction (Stage 3) and analytics aggregation (Stage 4) haven't been run
  yet, and there's no API layer or DB schema serving it)
- Auth, saved-jobs persistence, and any real AI calls (CV parsing, the AI
  assistant) — `analyzeCV()` and `matchJobToCV()` are deterministic mocks
  today, structured so an AI call can drop in behind them later
- Career Insights, Salary Insights, and AI Assistant pages — present in the
  sidebar as "coming soon" placeholders so the navigation already reflects
  the full product, but not built out
