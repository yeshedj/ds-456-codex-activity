"""Compare offense composition using incident start dates and recorded HHMM."""

import csv
from collections import Counter
from datetime import date, time, timedelta
import math

from explore_police import ROOT, OUT, save_chart
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

NIGHT = "Weekend nights"
WORK = "Weekday working hours"
OTHER = "Outside selected windows"


def top_five_with_ties(counts):
    """Select five positive-count categories, including all ties at fifth."""
    return counts.loc[counts.gt(0)].nlargest(5, keep="all").index.tolist()


def main():
    source = ROOT / "data/Police_Incidents_2026.csv"
    df = pd.read_csv(source, dtype={"caseNumber": "string", "beginTime": "string"})
    # Read the published calendar date literally, without interpreting its offset
    # or converting it to another time zone. HHMM is also used unchanged.
    calendar_date = df.beginDate.astype("string").str.slice(0, 10).str.replace("/", "-", regex=False)
    start_date = pd.to_datetime(calendar_date, format="%Y-%m-%d", errors="coerce")
    hhmm = pd.to_numeric(df.beginTime, errors="coerce")
    valid_time = hhmm.notna() & hhmm.mod(1).eq(0) & hhmm.between(0, 2359) & hhmm.mod(100).lt(60)
    in_period = start_date.ge("2026-01-01") & start_date.lt("2026-10-01")
    eligible = in_period & valid_time
    minutes = (hhmm // 100) * 60 + hhmm.mod(100)
    weekday = start_date.dt.dayofweek  # Monday=0, Sunday=6
    night = eligible & ((weekday.isin([4, 5]) & minutes.ge(23 * 60)) |
                        (weekday.isin([5, 6]) & minutes.lt(4 * 60)))
    working = eligible & weekday.lt(5) & minutes.ge(9 * 60) & minutes.lt(17 * 60)
    assert not (night & working).any()
    window = pd.Series("Missing/invalid start date", index=df.index)
    window.loc[start_date.notna() & ~in_period] = "Start date outside January–September"
    window.loc[in_period & ~valid_time] = "Missing/invalid start time"
    window.loc[eligible] = OTHER
    window.loc[night] = NIGHT
    window.loc[working] = WORK
    description = df.description.fillna("Unknown")
    classified = df[["OBJECTID", "caseNumber", "beginDate", "beginTime", "description", "neighborhood"]].copy()
    classified["description"] = description
    classified["window"] = window
    classified.to_csv(OUT / "time_window_assignments.csv", index=False)

    counts = pd.crosstab(description, window).reindex(columns=[NIGHT, WORK], fill_value=0)
    denominators = counts.sum()
    if denominators.eq(0).any():
        raise ValueError("Both comparison windows need at least one eligible incident.")
    shares = counts.div(denominators, axis=1) * 100
    assert all(math.isclose(float(total), 100.0, abs_tol=1e-9) for total in shares.sum())
    assert int(denominators[NIGHT]) == int(night.sum())
    assert int(denominators[WORK]) == int(working.sum())
    comparison = pd.DataFrame({
        "weekend_night_count": counts[NIGHT], "weekend_night_percent": shares[NIGHT],
        "weekday_work_count": counts[WORK], "weekday_work_percent": shares[WORK],
        "night_minus_work_percentage_points": shares[NIGHT] - shares[WORK],
        "weekend_night_rank": counts[NIGHT].where(counts[NIGHT].gt(0)).rank(method="min", ascending=False),
        "weekday_work_rank": counts[WORK].where(counts[WORK].gt(0)).rank(method="min", ascending=False),
    })
    comparison.to_csv(OUT / "time_window_offense_comparison.csv")
    # Union avoids concealing a category that is common in only one window.
    selected = set(top_five_with_ties(counts[NIGHT])) | set(top_five_with_ties(counts[WORK]))
    order = counts.sum(axis=1).sort_values(ascending=False, kind="stable").index
    selected = [name for name in order if name in selected]

    sns.set_theme(style="whitegrid", rc={"axes.titleweight": "bold", "figure.constrained_layout.use": True})
    chart = shares.loc[selected].reset_index().melt(id_vars="description", var_name="window", value_name="percent")
    fig, ax = plt.subplots(figsize=(12, 6.5))
    sns.barplot(data=chart, y="description", x="percent", hue="window", order=selected,
                hue_order=[NIGHT, WORK], palette=["#347A92", "#D58047"], errorbar=None, ax=ax)
    for container in ax.containers:
        ax.bar_label(container, fmt="%.1f%%", padding=4, fontsize=10)
    ax.set_xlim(0, chart.percent.max() * 1.2)
    ax.set_xlabel("Percentage of all incidents within each selected window")
    ax.set_ylabel("")
    ax.set_title(f"Offense composition differs across recorded time windows\nJan–Sep 2026 starts | Weekend nights n={denominators[NIGHT]:,}; working hours n={denominators[WORK]:,}", loc="left", pad=18)
    ax.legend(title="Source-recorded clock times", loc="lower right")
    ax.grid(axis="y", visible=False)
    sns.despine(ax=ax, left=True)
    save_chart(fig, "09_time_window_offense_shares.png")

    # 0000 is valid midnight, but it may also be a rounded/default value. Keep it
    # in the main analysis, then show a transparent sensitivity comparison.
    night_without_midnight = night & hhmm.ne(0)
    sensitivity_counts = description.loc[night_without_midnight].value_counts()
    sensitivity = comparison[["weekend_night_count", "weekend_night_percent"]].copy()
    sensitivity["night_count_without_0000"] = sensitivity_counts.reindex(sensitivity.index, fill_value=0)
    sensitivity["night_percent_without_0000"] = 100 * sensitivity.night_count_without_0000 / night_without_midnight.sum()
    sensitivity["change_percentage_points"] = sensitivity.night_percent_without_0000 - sensitivity.weekend_night_percent
    sensitivity["main_night_rank"] = comparison.weekend_night_rank
    sensitivity["rank_without_0000"] = sensitivity.night_count_without_0000.where(
        sensitivity.night_count_without_0000.gt(0)).rank(method="min", ascending=False)
    assert sensitivity.night_count_without_0000.sum() == night_without_midnight.sum()
    assert math.isclose(float(sensitivity.night_percent_without_0000.sum()), 100.0, abs_tol=1e-9)
    sensitivity.to_csv(OUT / "time_window_midnight_sensitivity.csv")

    audit = pd.Series({
        "original_records": len(df), "missing_or_unparseable_start_date": int(start_date.isna().sum()),
        "valid_start_date_outside_period": int((start_date.notna() & ~in_period).sum()),
        "invalid_start_time_in_period": int((in_period & ~valid_time).sum()),
        "eligible_jan_sep_start_records": int(eligible.sum()), "weekend_nights": int(night.sum()),
        "weekday_working_hours": int(working.sum()), "eligible_outside_both_windows": int((eligible & ~night & ~working).sum()),
        "missing_descriptions_in_selected_windows": int((df.description.isna() & (night | working)).sum()),
        "weekend_night_records_at_0000": int((night & hhmm.eq(0)).sum()),
    }, name="records")
    assert len(df) == (audit.missing_or_unparseable_start_date + audit.valid_start_date_outside_period
                       + audit.invalid_start_time_in_period + audit.eligible_jan_sep_start_records)
    assert audit.eligible_jan_sep_start_records == (audit.weekend_nights + audit.weekday_working_hours
                                                   + audit.eligible_outside_both_windows)
    audit.to_csv(OUT / "time_window_filter_audit.csv", index_label="filter")

    # Independent reference: CSV reader + Python date/time, assigning overnight
    # incidents to the preceding evening. This differs from the vectorized mask.
    reference = {NIGHT: Counter(), WORK: Counter()}
    raw_records = []
    with source.open(newline="") as handle:
        for source_index, row in enumerate(csv.DictReader(handle)):
            try:
                day = date.fromisoformat(row["beginDate"][:10].replace("/", "-"))
                value = float(row["beginTime"])
                if not math.isfinite(value) or not value.is_integer():
                    continue
                clock = time(int(value) // 100, int(value) % 100)
            except (ValueError, TypeError):
                continue
            if not date(2026, 1, 1) <= day < date(2026, 10, 1):
                continue
            evening = day - timedelta(days=1) if clock < time(4) else day
            label = OTHER
            if (clock >= time(23) or clock < time(4)) and evening.weekday() in (4, 5):
                label = NIGHT
            elif day.weekday() < 5 and time(9) <= clock < time(17):
                label = WORK
            row.update({"expected_window": label, "weekday": day.weekday(), "source_index": source_index})
            raw_records.append(row)
            if label in reference:
                reference[label][row["description"] or "Unknown"] += 1
    for label in reference:
        assert sum(reference[label].values()) == denominators[label]
        assert reference[label] == Counter({k: int(v) for k, v in counts[label].items() if v})

    # Explicit expectations follow directly from the reviewed half-open windows.
    examples = [
        (4, 2300, NIGHT, "Friday 23:00 starts a weekend-night window"),
        (5, 0, NIGHT, "Saturday 00:00 belongs to Friday night"),
        (6, 0, NIGHT, "Sunday 00:00 belongs to Saturday night"),
        (4, 0, OTHER, "Friday 00:00 belongs to Thursday night"),
        (5, 400, OTHER, "Saturday 04:00 is the excluded endpoint"),
        (0, 900, WORK, "Monday 09:00 is included"),
        (4, 1700, OTHER, "Friday 17:00 is the excluded endpoint"),
        (5, 900, OTHER, "Saturday 09:00 is not a weekday"),
    ]
    boundary_rows = []
    for day_number, raw_time, expected, basis in examples:
        row = next((r for r in raw_records if r["weekday"] == day_number and int(r["beginTime"]) == raw_time), None)
        if row is None:
            continue
        actual = window.loc[row["source_index"]]
        assert actual == expected
        boundary_rows.append({"caseNumber": row["caseNumber"], "beginDate": row["beginDate"],
                              "beginTime": row["beginTime"], "basis": basis,
                              "expected_window": expected, "observed_window": actual})
    pd.DataFrame(boundary_rows).to_csv(OUT / "time_window_boundary_checks.csv", index=False)

    table = "\n".join(
        f"| {name} | {comparison.loc[name, 'weekend_night_count']:,} ({comparison.loc[name, 'weekend_night_percent']:.1f}%) | {comparison.loc[name, 'weekday_work_count']:,} ({comparison.loc[name, 'weekday_work_percent']:.1f}%) | {comparison.loc[name, 'night_minus_work_percentage_points']:+.1f} |"
        for name in selected)
    sensitivity_table = "\n".join(
        f"| {name} | {sensitivity.loc[name, 'weekend_night_percent']:.1f}% | {sensitivity.loc[name, 'night_percent_without_0000']:.1f}% |"
        for name in dict.fromkeys(selected + top_five_with_ties(sensitivity_counts)))
    example_table = "\n".join(f"| {r['caseNumber']} | {r['beginDate'][:10]} | {int(r['beginTime']):04d} | {r['basis']} | {r['observed_window']} |" for r in boundary_rows)
    verification = f"""# Verifying time-window assignments

**Basis of the check:** Friday/Saturday nights include the following morning until 04:00, exclusive. Working hours include Monday–Friday from 09:00, inclusive, to 17:00, exclusive. These definitions establish the expectations below independently of the plotted percentages.

| Case number | Recorded start date | HHMM | Expected from interval definition | Observed assignment |
|---|---|---:|---|---|
{example_table}

All {len(boundary_rows)} source-record comparisons passed. Inspect these identified rows in the original CSV and their calendar weekdays when documenting your own verification.

A separate calculation uses Python's CSV reader and date/time objects, assigning early-morning incidents to the preceding evening. It matches **all offense counts**, **{night.sum():,} weekend-night records**, and **{working.sum():,} working-hour records**. Automobile theft's weekend-night share is independently reconstructed as **{reference[NIGHT]['AUTOMOBILE THEFT']:,} / {sum(reference[NIGHT].values()):,} × 100 = {100 * reference[NIGHT]['AUTOMOBILE THEFT'] / sum(reference[NIGHT].values()):.2f}%**, matching the main calculation.

The record accounting checks pass: **{len(df):,} = {start_date.isna().sum():,} invalid dates + {(start_date.notna() & ~in_period).sum():,} dates outside the period + {(in_period & ~valid_time).sum():,} invalid times within the period + {eligible.sum():,} eligible records**. The eligible records split into **{night.sum():,} night + {working.sum():,} working hours + {(eligible & ~night & ~working).sum():,} other hours**. All-description percentages sum to **{shares[NIGHT].sum():.6f}%** and **{shares[WORK].sum():.6f}%**. Excluding midnight, nighttime percentages sum to **{sensitivity.night_percent_without_0000.sum():.6f}%**.

**Section 7.3 scope:** these checks use the agreed recorded-calendar-date and recorded-HHMM assumption. They do not verify the source time zone, Minneapolis local-time interpretation, or the accuracy of the recorded incident times. The separate algorithm and explicit source-record comparisons provide evidence beyond successful script execution; inspect the evidence before writing your personal reflection.

[Boundary records](outputs/time_window_boundary_checks.csv) · [All row assignments](outputs/time_window_assignments.csv). This verifies implementation against the stated recorded-clock definitions; it does not resolve the source time zone or uncertain incident times.
"""
    (ROOT / "analysis/time_window_verification.md").write_text(verification)
    main_top = set(top_five_with_ties(counts[NIGHT]))
    sensitivity_top = set(top_five_with_ties(sensitivity_counts))
    entered = ", ".join(sorted(sensitivity_top - main_top)) or "None"
    left = ", ".join(sorted(main_top - sensitivity_top)) or "None"
    night_leaders = " / ".join(counts.index[counts[NIGHT].eq(counts[NIGHT].max())])
    work_leaders = " / ".join(counts.index[counts[WORK].eq(counts[WORK].max())])
    report = f"""# Weekend nights versus weekday working hours

**Question:** Among incidents with valid recorded start dates and times in January–September 2026, how do the most common offense descriptions and their percentage shares differ between the two windows?

**Agreed assumption:** use the calendar date in `beginDate` and HHMM in `beginTime` **as recorded, without time-zone conversion**. These are recorded-clock comparisons, not confirmed Minneapolis local-time comparisons.

## Method

- Keep start dates January 1–September 30. Validate HHMM (hours 00–23, minutes 00–59); `30` means 00:30.
- Weekend nights: Friday 23:00–Saturday 04:00 and Saturday 23:00–Sunday 04:00. Working hours: Monday–Friday 09:00–17:00. Include starts and exclude endpoints.
- Count every description and divide by **all incidents in its window**. Keep missing descriptions as Unknown. Neighborhood, coordinate, and UCR-code missingness does not exclude records.
- Plot the union of each window's top five descriptions, including ties at fifth place. Reuse the exploration's Seaborn style; the [earlier maps](mapping_summary.md) provide geographic context without requiring another spatial join.

## Results

**{eligible.sum():,} eligible records:** {night.sum():,} weekend nights, {working.sum():,} working hours, and {(eligible & ~night & ~working).sum():,} outside both windows. Of {len(df):,} source rows, {start_date.isna().sum():,} have invalid/missing dates, {(start_date.notna() & ~in_period).sum():,} have dates outside January–September, and {(in_period & ~valid_time).sum():,} have invalid/missing times within the period. [Audit](outputs/time_window_filter_audit.csv)

![Recorded-clock offense shares](outputs/09_time_window_offense_shares.png)

| Description | Weekend nights (n={night.sum():,}) | Working hours (n={working.sum():,}) | Night minus work (percentage points) |
|---|---:|---:|---:|
{table}

**Leading descriptions:** {night_leaders} at night; {work_leaders} during working hours. Displayed categories need not total 100%; denominators include all categories. [Complete comparison](outputs/time_window_offense_comparison.csv)

## Midnight sensitivity

Keep `0000` as valid midnight in the main analysis. Excluding **{(night & hhmm.eq(0)).sum():,} midnight entries ({100 * (night & hhmm.eq(0)).sum() / night.sum():.1f}% of night records)** leaves **{night_without_midnight.sum():,}** night records; working hours are unchanged. Midnight could reflect an exact, rounded, or default value—the CSV does not distinguish these.

| Description | Main night share | Excluding 0000 |
|---|---:|---:|
{sensitivity_table}

**Nighttime top-five changes:** entered: {entered}; left: {left}. [All sensitivity counts, shares, and ranks](outputs/time_window_midnight_sensitivity.csv)

## Verification and interpretation

Record accounting and all-description share checks pass. An independent CSV/date-time algorithm matches every offense count and both denominators. **{len(boundary_rows)} identified source-record checks** confirm overnight and endpoint handling; see [Section 7.3 verification evidence](time_window_verification.md).

The verification checks calculations **under the recorded-clock assumption**; it does not establish the source time zone or time accuracy. These results describe offense composition, not overall peak hours, per-hour rates, or causes. The snapshot's reporting coverage ends October 21, so delayed and unreported incidents can affect completeness.

Run `.venv/bin/python analysis/compare_time_windows.py` to rebuild. [Per-record assignments](outputs/time_window_assignments.csv) include original case numbers, start values, and the assigned group or exclusion reason.
"""
    (ROOT / "analysis/time_window_summary.md").write_text(report)
    print(audit.to_string())
    print(comparison.loc[selected].round(2).to_string())
    print("Independent count and source-record boundary checks passed.")


if __name__ == "__main__":
    main()
