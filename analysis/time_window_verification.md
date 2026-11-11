# Verifying time-window assignments

**Basis of the check:** Friday/Saturday nights include the following morning until 04:00, exclusive. Working hours include Monday–Friday from 09:00, inclusive, to 17:00, exclusive. These definitions establish the expectations below independently of the plotted percentages.

| Case number | Recorded start date | HHMM | Expected from interval definition | Observed assignment |
|---|---|---:|---|---|
| MP2026703163 | 2026/03/06 | 2300 | Friday 23:00 starts a weekend-night window | Weekend nights |
| MP2026702105 | 2026/02/14 | 0000 | Saturday 00:00 belongs to Friday night | Weekend nights |
| MP202639578 | 2026/02/15 | 0000 | Sunday 00:00 belongs to Saturday night | Weekend nights |
| MP2026701995 | 2026/02/13 | 0000 | Friday 00:00 belongs to Thursday night | Outside selected windows |
| MP202670140 | 2026/03/21 | 0400 | Saturday 04:00 is the excluded endpoint | Outside selected windows |
| MP2026701422 | 2026/01/05 | 0900 | Monday 09:00 is included | Weekday working hours |
| MP202639834 | 2026/01/16 | 1700 | Friday 17:00 is the excluded endpoint | Outside selected windows |
| MP202638098 | 2026/02/14 | 0900 | Saturday 09:00 is not a weekday | Outside selected windows |

All 8 source-record comparisons passed. Inspect these identified rows in the original CSV and their calendar weekdays when documenting your own verification.

A separate calculation uses Python's CSV reader and date/time objects, assigning early-morning incidents to the preceding evening. It matches **all offense counts**, **1,395 weekend-night records**, and **4,219 working-hour records**. Automobile theft's weekend-night share is independently reconstructed as **300 / 1,395 × 100 = 21.51%**, matching the main calculation.

The record accounting checks pass: **18,904 = 0 invalid dates + 1,338 dates outside the period + 0 invalid times within the period + 17,566 eligible records**. The eligible records split into **1,395 night + 4,219 working hours + 11,952 other hours**. All-description percentages sum to **100.000000%** and **100.000000%**. Excluding midnight, nighttime percentages sum to **100.000000%**.

**Section 7.3 scope:** these checks use the agreed recorded-calendar-date and recorded-HHMM assumption. They do not verify the source time zone, Minneapolis local-time interpretation, or the accuracy of the recorded incident times. The separate algorithm and explicit source-record comparisons provide evidence beyond successful script execution; inspect the evidence before writing your personal reflection.

[Boundary records](outputs/time_window_boundary_checks.csv) · [All row assignments](outputs/time_window_assignments.csv). This verifies implementation against the stated recorded-clock definitions; it does not resolve the source time zone or uncertain incident times.
