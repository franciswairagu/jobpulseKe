# JobPulse — Field & Date Reliability Audit

_Generated 2026-09-05T15:00:21_

## Field Completeness

Missingness is concentrated by source, not random. Fields below `country` and `work_mode` should not be used for whole-dataset analysis without filtering to the sources that actually populate them.

| source            |   n_rows |   date_posted_pct_populated |   salary_pct_populated |   currency_pct_populated |   experience_required_pct_populated |   education_required_pct_populated |   tech_category_pct_populated |   job_field_pct_populated |   employment_type_pct_populated |   country_pct_populated |   work_mode_pct_populated |
|:------------------|---------:|----------------------------:|-----------------------:|-------------------------:|------------------------------------:|-----------------------------------:|------------------------------:|--------------------------:|--------------------------------:|------------------------:|--------------------------:|
| ALL               |    10379 |                        17.2 |                    1.7 |                      0.6 |                                 5.2 |                                6.3 |                          76.6 |                       9   |                             7.8 |                     100 |                       100 |
| fantastic_jobs_hf |     5374 |                         0   |                    0   |                      0   |                                 0   |                                0   |                         100   |                       0   |                             0   |                     100 |                       100 |
| jobberman         |     1939 |                         0   |                    0   |                      0   |                                 0   |                                0   |                          12.7 |                       0   |                             0   |                     100 |                       100 |
| linkedin          |     1147 |                       100   |                    0   |                      0   |                                 0   |                                0   |                          80.5 |                       0   |                             0   |                     100 |                       100 |
| hotnigerianjobs   |      813 |                        56.6 |                   14.1 |                      0   |                                 0   |                                0   |                          44.6 |                       0   |                             0   |                     100 |                       100 |
| myjobmag          |      654 |                         1.8 |                    2.6 |                      2.3 |                                77.1 |                               99.7 |                         100   |                      99.8 |                            99.8 |                     100 |                       100 |
| indeed            |      110 |                         0   |                    0   |                      0   |                                 0   |                                0   |                          78.2 |                       0   |                             0   |                     100 |                       100 |
| fuzu              |       90 |                         0   |                    0   |                      0   |                                 0   |                                0   |                          98.9 |                      98.9 |                            58.9 |                     100 |                       100 |
| brightermonday    |       74 |                         0   |                   12.2 |                      9.5 |                                 0   |                                0   |                          62.2 |                     100   |                             0   |                     100 |                       100 |
| jobicy            |       71 |                       100   |                   33.8 |                     57.7 |                                56.3 |                                0   |                         100   |                      56.3 |                           100   |                     100 |                       100 |
| weworkremotely    |       67 |                       100   |                    0   |                      0   |                                 0   |                                0   |                          98.5 |                     100   |                             0   |                     100 |                       100 |
| remoteok          |       25 |                       100   |                   16   |                      0   |                                 0   |                                0   |                          88   |                       0   |                           100   |                     100 |                       100 |
| jobwebkenya       |        7 |                         0   |                    0   |                      0   |                                 0   |                                0   |                           0   |                     100   |                             0   |                     100 |                       100 |
| remotive          |        6 |                       100   |                   50   |                     50   |                                 0   |                                0   |                         100   |                     100   |                           100   |                     100 |                       100 |
| talent_com        |        2 |                         0   |                    0   |                      0   |                                 0   |                                0   |                          50   |                       0   |                             0   |                     100 |                       100 |


## date_posted Reliability

A `(source, date)` pair shared by 5+ unrelated postings is flagged as a likely batch/import artifact rather than a genuine per-listing timestamp, and excluded from the trustworthy subset.

| source          |   dated_rows |   distinct_dates |   avg_rows_per_date |   trustworthy_rows |   trustworthy_pct |
|:----------------|-------------:|-----------------:|--------------------:|-------------------:|------------------:|
| linkedin        |         1147 |              207 |                 5.5 |                257 |              22.4 |
| hotnigerianjobs |          460 |               44 |                10.5 |                 16 |               3.5 |
| jobicy          |           71 |                2 |                35.5 |                  0 |               0   |
| weworkremotely  |           67 |               26 |                 2.6 |                 41 |              61.2 |
| remoteok        |           25 |                6 |                 4.2 |                 11 |              44   |
| myjobmag        |            8 |                8 |                 1   |                  8 |             100   |
| remotive        |            6 |                6 |                 1   |                  6 |             100   |


**Trustworthy dated rows (whole dataset): 339**

Bootstrap 95% CI for median posting age on the trustworthy subset: observed = 96 days, CI = [87, 109] days (n=339, 2000 resamples).


## Recommendations

- Do not build trend, salary, or experience-level analysis on the full dataset without first checking this report's completeness table.
- `date_posted` needs a scraper-level fix for `fantastic_jobs_hf`, `jobberman`, `brightermonday`, `fuzu`, `indeed`, `jobwebkenya` — these sources never capture it, at ingestion or after cleaning.
- Treat `date_posted` as unreliable for any (source, date) pair with 5+ postings; only the trustworthy subset should feed time-based analysis.
- `salary`, `experience_required`, `education_required`, `job_field`, `employment_type` are all >90% missing dataset-wide — flag to teammates building Stage 4/5/6 on these fields.
