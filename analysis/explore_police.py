"""Explore the local police CSV. Run: .venv/bin/python analysis/explore_police.py"""

from pathlib import Path
import os

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "analysis" / "outputs"
OUT.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".venv" / "matplotlib-cache"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.ticker import StrMethodFormatter


def save_chart(fig, filename):
    fig.savefig(OUT / filename, dpi=160, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def count_bars(ax, counts, color, horizontal=False):
    """Plot precomputed counts; no estimation or uncertainty intervals needed."""
    labels = counts.index.astype(str).tolist()
    sns.barplot(
        x=counts.values if horizontal else labels,
        y=labels if horizontal else counts.values,
        orient="h" if horizontal else "v", color=color,
        errorbar=None, saturation=1, width=0.7, ax=ax,
    )
    ax.bar_label(ax.containers[0], labels=[f"{v:,}" for v in counts],
                 padding=5, fontsize=10, color="#344256")
    ax.set_axisbelow(True)
    ax.grid(axis="y" if horizontal else "x", visible=False)
    axis = ax.xaxis if horizontal else ax.yaxis
    axis.set_major_formatter(StrMethodFormatter("{x:,.0f}"))
    sns.despine(ax=ax, left=True, bottom=True)


def main():
    source = ROOT / "data" / "Police_Incidents_2026.csv"
    # Codes and identifiers are labels, even when they contain only digits.
    # Keep missing cells as missing: never drop every row with any missing field.
    df = pd.read_csv(source, keep_default_na=True, dtype={
        "caseNumber": "string", "precinct": "string", "UCRCode": "string",
        "offense": "string", "OBJECTID": "string",
    })
    n = len(df)
    profile = pd.DataFrame({
        "column": df.columns,
        "loaded_dtype": [str(df[c].dtype) for c in df],
        "nonmissing_unique": [df[c].nunique() for c in df],
        "missing": [df[c].isna().sum() for c in df],
        "missing_percent": [100 * df[c].isna().mean() for c in df],
    })
    profile.to_csv(OUT / "column_summary.csv", index=False)

    # Preserve the source's calendar dates. Do not convert date-only midnight
    # values to Chicago time: doing so would shift them to the previous day.
    dates = {c: pd.to_datetime(df[c], utc=True, errors="coerce") for c in [
        "reportedDate", "beginDate", "reportedDateTime", "enteredDate",
        "lastchanged", "LastUpdateDateETL",
    ]}
    date_profile = pd.DataFrame([
        {"column": c, "earliest_utc": s.min(), "latest_utc": s.max(),
         "missing_in_source": df[c].isna().sum(),
         "unparseable_nonmissing": (s.isna() & df[c].notna()).sum()}
        for c, s in dates.items()
    ])
    date_profile.to_csv(OUT / "date_summary.csv", index=False)

    # Unknown is a display/grouping label, not an estimated replacement value.
    # These temporary Series leave missing cells in the source DataFrame intact.
    descriptions = df["description"].fillna("Unknown").value_counts()
    descriptions.rename_axis("description").rename("records").to_csv(OUT / "offense_counts.csv")
    neighborhoods = df["neighborhood"].fillna("Unknown").value_counts()
    neighborhoods.rename_axis("neighborhood").rename("records").to_csv(OUT / "neighborhood_counts.csv")

    first = dates["reportedDate"].min()
    last = dates["reportedDate"].max()
    first_month = first.strftime("%Y-%m")
    last_month = last.strftime("%Y-%m")
    month_index = pd.period_range(first_month, last_month, freq="M").astype(str)
    # Missing/unparseable reported dates cannot be assigned to a month. Count
    # them explicitly for the report rather than silently treating them as zero.
    months = dates["reportedDate"].dt.strftime("%Y-%m")
    monthly = pd.DataFrame({
        "records": months.value_counts().reindex(month_index, fill_value=0),
        "bike_theft_records": months[df["offense"].eq("BIKETF")].value_counts().reindex(month_index, fill_value=0),
    }).rename_axis("reported_month")
    monthly["bike_theft_percent"] = 100 * monthly.bike_theft_records / monthly.records
    # Boundary months may be incomplete, even when an end date is month-end.
    monthly["boundary_month"] = monthly.index.isin([first_month, last_month])
    monthly.to_csv(OUT / "monthly_counts.csv")

    # A reporting gap requires both dates. Pandas leaves an unavailable gap as
    # NaN; mean/median skip it. Use valid gaps as percentage denominators too.
    lag = (dates["reportedDate"] - dates["beginDate"]).dt.days
    delay_bins = pd.cut(lag, [-np.inf, -1, 0, 1, 7, 30, 365, np.inf], labels=[
        "Negative", "Same date", "1 day", "2–7 days", "8–30 days", "31–365 days", ">365 days",
    ])
    delay_counts = delay_bins.value_counts(sort=False)
    if lag.isna().any():
        delay_counts.loc["Unknown dates"] = lag.isna().sum()
    delay_counts.rename_axis("calendar_date_gap").rename("records").to_csv(OUT / "reporting_delay_counts.csv")
    delays_by_type = df.assign(calendar_days=lag).groupby("offense").agg(
        records=("calendar_days", "size"), valid_date_pairs=("calendar_days", "count"),
        median_days=("calendar_days", "median"),
        over_30_days=("calendar_days", lambda s: s.gt(30).sum()),
    )
    delays_by_type["over_30_days_percent"] = 100 * delays_by_type.over_30_days / delays_by_type.valid_date_pairs
    delays_by_type.to_csv(OUT / "delays_by_offense.csv")

    sns.set_theme(style="whitegrid", context="notebook", font_scale=1.05, rc={
        "axes.titleweight": "bold", "axes.titlepad": 16,
        "axes.labelcolor": "#344256", "text.color": "#25344A",
        "grid.color": "#E8EDF2", "grid.linewidth": 0.8,
        "figure.constrained_layout.use": True,
    })
    blue, orange = "#347A92", "#D58047"

    fig, ax = plt.subplots(figsize=(10, 6))
    top = descriptions.head(10)
    count_bars(ax, top, blue, horizontal=True)
    ax.set_xlim(0, top.max() * 1.16)
    ax.set_xlabel("Records in the local CSV")
    ax.set_ylabel("")
    ax.set_title("Automobile theft leads the ten most common categories", loc="left")
    save_chart(fig, "01_offense_categories.png")

    fig, axes = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
    positions = np.arange(len(monthly))
    count_bars(axes[0], monthly.records, blue)
    axes[0].patches[-1].set_facecolor(orange)
    axes[0].set_ylabel("All records")
    axes[0].set_title(f"Monthly reports | {first:%b %d}–{last:%b %d, %Y}\nOrange marks the incomplete final month", loc="left")
    axes[0].set_ylim(0, monthly.records.max() * 1.18)
    sns.lineplot(x=positions, y=monthly.bike_theft_percent.to_numpy(),
                 marker="o", markersize=8, linewidth=2.5, color=blue,
                 errorbar=None, ax=axes[1])
    axes[1].scatter(positions[-1], monthly.bike_theft_percent.iloc[-1],
                    color=orange, s=65, zorder=4)
    for pos, value in zip(positions, monthly.bike_theft_percent):
        axes[1].annotate(f"{value:.1f}%", (pos, value), xytext=(0, 9), textcoords="offset points", ha="center", fontsize=9)
    axes[1].set_ylabel("Bike theft / all records (%)")
    axes[1].set_title("Bike theft's share rises in summer", loc="left")
    axes[1].set_ylim(0, monthly.bike_theft_percent.max() * 1.3)
    axes[1].set_xticks(positions, [pd.Timestamp(m).strftime("%b") for m in monthly.index])
    axes[1].set_xlabel("Reported month (source calendar date)")
    axes[1].grid(axis="x", visible=False)
    sns.despine(ax=axes[1], left=True, bottom=True)
    save_chart(fig, "02_monthly_patterns.png")

    fig, ax = plt.subplots(figsize=(10, 5))
    # Keep the negative-gap validation in the table, but hide its empty bar.
    plotted_delays = delay_counts.drop("Negative") if delay_counts.loc["Negative"] == 0 else delay_counts
    count_bars(ax, plotted_delays, blue)
    ax.set_ylim(0, plotted_delays.max() * 1.18)
    ax.set_ylabel("Records")
    ax.set_xlabel("Reported date minus begin date (calendar days)")
    ax.set_title(f"Long reporting gaps pull up the average\nMedian {lag.median():.0f} days | Mean {lag.mean():.1f} days | Maximum {lag.max():,.0f} days", loc="left")
    save_chart(fig, "03_reporting_delays.png")

    fig, ax = plt.subplots(figsize=(10, 6))
    top_neighborhoods = neighborhoods.head(10)
    count_bars(ax, top_neighborhoods, blue, horizontal=True)
    ax.set_xlim(0, top_neighborhoods.max() * 1.15)
    ax.set_xlabel("Records (counts are not population-adjusted rates)")
    ax.set_ylabel("")
    ax.set_title("Downtown West leads the ten largest neighborhood counts", loc="left")
    save_chart(fig, "04_neighborhood_counts.png")

    bike_start, bike_aug = monthly.loc["2026-01"], monthly.loc["2026-08"]
    valid_lags = lag.notna().sum()
    missing_counts = df.isna().sum()
    report = f"""# Minneapolis police incidents: a first look

The local CSV contains **{n:,} records and {len(df.columns)} columns**, covering reports from **{first:%B %d} to {last:%B %d, %Y}**. It has {df.description.nunique()} offense descriptions and {df.neighborhood.nunique()} named neighborhoods, with {df.caseNumber.duplicated().sum()} repeated case numbers.

Variables include offense categories, dates, neighborhoods, and numeric coordinates. Identifiers and codes are treated as text; dates are parsed explicitly. [Column details](outputs/column_summary.csv) · [Date checks](outputs/date_summary.csv)

## Missing values: what we do and why

Pandas recognizes empty cells and standard missing markers such as `NA` when reading the CSV. We **retain all {n:,} rows** and never guess missing codes or locations.

| Field | Missing | Treatment |
|---|---:|---|
| `centergbsid` | {missing_counts['centergbsid']:,} (100%) | Leave empty and do not use it in summaries. Dropping rows because this field is missing would erase the dataset. |
| `UCRCode` | {missing_counts['UCRCode']:,} ({100 * missing_counts['UCRCode'] / n:.2f}%) | Leave missing; category charts use the available `description` instead. |
| `neighborhood` | {missing_counts['neighborhood']:,} ({100 * missing_counts['neighborhood'] / n:.2f}%) | Count as **Unknown** in the neighborhood table; it falls outside the chart's top ten. |

All other fields have no detected missing values. `Unknown` is a grouping label, not an inferred neighborhood. No blanket `dropna()` or imputation is used.

Dates that cannot be parsed become missing dates and are counted in the [date checks](outputs/date_summary.csv). Monthly summaries require a valid reported date; reporting gaps require both reported and begin dates. Means, medians, and gap percentages use valid date pairs only. In this file, **{dates['reportedDate'].isna().sum()} rows are excluded from monthly counts and {lag.isna().sum()} from gap calculations**.

## Four patterns

**1. A few offense categories dominate.** Automobile theft accounts for **{descriptions['AUTOMOBILE THEFT']:,} records ({100 * descriptions['AUTOMOBILE THEFT'] / n:.1f}%)**. The three largest categories together make up **{100 * descriptions.head(3).sum() / n:.1f}%** of records.

![Most common offense descriptions](outputs/01_offense_categories.png)

**2. Bike theft increases sharply in summer.** January has **{int(bike_start.bike_theft_records)} reports**, compared with **{int(bike_aug.bike_theft_records)} in August**. Its share of all reports grows from **{bike_start.bike_theft_percent:.2f}% to {bike_aug.bike_theft_percent:.2f}%**, so this exceeds the change in overall reporting volume. This pattern does not establish its cause.

![Monthly reports and bike theft share](outputs/02_monthly_patterns.png)

**3. Reporting gaps have a long tail.** The median is **{lag.median():.0f} days**, but the mean is **{lag.mean():.2f} days**. **{lag.gt(30).sum():,} reports ({100 * lag.gt(30).sum() / valid_lags:.2f}%)** have gaps over 30 days. These are calendar-date differences; zero days means the same date, not immediate reporting. **{dates['beginDate'].dt.year.lt(2026).sum()} incidents began before 2026**.

Date-order check: **{lag.lt(0).sum()} negative gaps**. The empty category is omitted from the chart.

![Reporting gaps](outputs/03_reporting_delays.png)

**4. Neighborhood counts differ.** Downtown West has **{neighborhoods['Downtown West']:,} records**, followed by Whittier with **{neighborhoods['Whittier']:,}**. Counts do not measure resident risk or adjust for population and visitors.

![Neighborhood counts](outputs/04_neighborhood_counts.png)

## Read these charts carefully

- **October is incomplete:** coverage stops on October 21, so its lower count is not a comparable monthly decline. Month lengths also differ.
- Dates retain their source calendar dates; no local hour-of-day analysis is attempted.
- Results describe this local file, which differs from the changing live API.

To regenerate the report, tables, and Seaborn charts: `.venv/bin/python analysis/explore_police.py`. Dependencies are in [requirements.txt](requirements.txt).

For neighborhood maps and incident-type heatmaps, see [mapping summary](mapping_summary.md).
"""
    (ROOT / "analysis" / "dataset_summary.md").write_text(report)
    print(f"Analyzed {n:,} rows; saved report, four charts, and summary tables in {OUT.parent}")


if __name__ == "__main__":
    main()
