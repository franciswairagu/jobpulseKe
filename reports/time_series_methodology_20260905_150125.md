# JobPulse — Time Series Analysis: Methodology & Findings

_Generated 2026-09-05T15:01:38_

## The core constraint

This dataset is a **single scrape taken on one day**, not a series of repeated collections. That has one unavoidable consequence for time series work: a one-time scrape of a live job board only contains postings that were **still active** on scrape day. Any posting created earlier and already closed is absent entirely. So raw 'postings per week' rises steeply toward the scrape date purely as an artifact of which listings were still live — this is **survivorship bias**, not a hiring trend. Reporting it as a trend would be wrong. The analysis below is built around this constraint, not in denial of it.

## Part A — What the current snapshot legitimately supports (REAL data)

Instead of a trend over calendar time, a single snapshot supports **posting-age (freshness) analysis**: for each still-live posting, how many days elapsed between its `date_posted` and the scrape. This is genuine time-referenced analysis and is immune to the survivorship problem, because it doesn't claim anything about postings that aren't in the data. Computed on the **trustworthy subset only** (n=325; batch-artifact dates excluded per the reliability audit). All medians carry bootstrap 95% CIs.


### Median posting age by tech category

| tech_category        |   n |   median_age_days |   ci95_low |   ci95_high |
|:---------------------|----:|------------------:|-----------:|------------:|
| Software Development | 129 |              94   |       67   |         107 |
| Other Tech           |  74 |              97.5 |       64.5 |         145 |
| Data & AI            |  41 |              88   |       56   |         116 |

### Median posting age by country

| country       |   n |   median_age_days |   ci95_low |   ci95_high |
|:--------------|----:|------------------:|-----------:|------------:|
| Nigeria       |  84 |             132   |       89.5 |       187.5 |
| South Africa  |  84 |              99   |       79   |       114.5 |
| Egypt         |  57 |              97   |       80   |       116   |
| Global Remote |  50 |              12   |        7.5 |        21   |
| Ghana         |  30 |             443.5 |      381   |       707   |
| Kenya         |  17 |             159   |       49   |       326   |

Note the substantive real finding: remote-eligible listings turn over much faster (far lower median age) than country-specific ones, and any country showing an implausibly high median (e.g. several hundred days) is a flag that batch-artifact dates remain in that slice and should be treated with caution rather than reported.

## Part B — What unlocks true trend analysis (SIMULATED demo)

**Everything in this section uses SIMULATED data. It is a methodology demonstration, not a market finding, and must never be presented as one.** Its purpose is to show the trend/seasonality/forecasting pipeline is built and correct, ready to run on real data once it exists.

The pipeline (STL decomposition into trend + weekly seasonality + residual, followed by a naive seasonal forecast) is applied to a simulated daily series with known planted structure. The saved `SIMULATED_trend_decomposition_*.csv` shows the pipeline recovering that structure — confirming the method works.

### What real data this pipeline needs (the actual deliverable)

For Part B to run on REAL data and produce a valid trend, Stage 9's scheduled scraper must build a **panel**, not overwrite a snapshot:

- Each scheduled run records every posting seen, with a `first_seen` date (the date this posting first appeared in any scrape).
- New postings are appended; existing ones are not duplicated (dedupe on `job_id`).
- Counting postings by `first_seen` week then gives a true new-postings-over-time series, free of survivorship bias, because every posting is counted at the moment it appeared regardless of whether it later closed.
- After ~4–6 weeks of runs there are enough distinct real cycles for the Part B pipeline to produce a trustworthy trend and short-horizon forecast. Until then, Part A is the honest analysis.
