"""Describe offense types at exactly repeated coordinate pairs in the local CSV."""

from collections import Counter
from explore_police import ROOT, OUT, save_chart
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import pandas as pd
import seaborn as sns


def main():
    df = pd.read_csv(ROOT / "data/Police_Incidents_2026.csv", dtype={"caseNumber": "string"})
    valid = df.centerLong.between(-180, 180) & df.centerLat.between(-90, 90)
    valid &= ~(df.centerLong.eq(0) & df.centerLat.eq(0))
    locations = df.loc[valid].copy()
    locations["description"] = locations.description.fillna("Unknown offense")
    keys = ["centerLong", "centerLat"]
    # Match the source coordinates exactly: no rounding, buffers, or clustering.
    counts = pd.crosstab([locations[c] for c in keys], locations.description)
    totals = counts.sum(axis=1)
    repeated = counts.loc[totals.gt(1)]
    repeated.to_csv(OUT / "repeated_location_offense_counts.csv")
    rows = []
    for pair, categories in repeated.iterrows():
        maximum = int(categories.max())
        names = categories.index[categories.eq(maximum)].tolist()
        subset = locations.loc[locations.centerLong.eq(pair[0]) & locations.centerLat.eq(pair[1])]
        neighborhoods = subset.neighborhood.fillna("Unknown").value_counts()
        rows.append({
            "centerLong": pair[0], "centerLat": pair[1], "total_reports": int(categories.sum()),
            "leading_description": " / ".join(names), "leading_count_per_type": maximum,
            "leading_percent_per_type": 100 * maximum / categories.sum(),
            "number_of_tied_leaders": len(names),
            "recorded_neighborhoods": "; ".join(f"{name}: {n}" for name, n in neighborhoods.items()),
        })
    result = pd.DataFrame(rows).sort_values(
        ["total_reports", "centerLong", "centerLat"], ascending=[False, True, True])
    result.to_csv(OUT / "repeated_location_summary.csv", index=False)
    top = result.head(10).reset_index(drop=True)

    # Independently reconcile site counts from raw rows using Counter.
    reference = Counter(zip(locations.centerLong, locations.centerLat))
    assert result.total_reports.sum() == sum(n for n in reference.values() if n > 1)
    assert dict(zip(zip(result.centerLong, result.centerLat), result.total_reports)) == {
        pair: n for pair, n in reference.items() if n > 1
    }
    for row in top.itertuples():
        assert reference[(row.centerLong, row.centerLat)] == row.total_reports
        source_types = Counter(locations.loc[
            locations.centerLong.eq(row.centerLong) & locations.centerLat.eq(row.centerLat), "description"])
        assert max(source_types.values()) == row.leading_count_per_type

    sns.set_theme(style="whitegrid", rc={"axes.titleweight": "bold", "figure.constrained_layout.use": True})
    types = top.leading_description.unique()
    colors = dict(zip(types, sns.color_palette("colorblind", len(types))))
    fig, ax = plt.subplots(figsize=(13, 8))
    y = range(len(top))
    ax.barh(y, top.total_reports, color="#E3E8EC", height=0.7)
    ax.barh(y, top.leading_count_per_type, color=[colors[t] for t in top.leading_description], height=0.7)
    for i, row in enumerate(top.itertuples()):
        ax.text(row.total_reports + 4, i,
                f"{row.leading_count_per_type}/{row.total_reports} ({row.leading_percent_per_type:.1f}%)", va="center", fontsize=10)
    ax.set_yticks(list(y), [f"{i+1}. ({row.centerLong:.5f}, {row.centerLat:.5f})" for i, row in enumerate(top.itertuples())])
    ax.invert_yaxis()
    ax.set_xlim(0, top.total_reports.max() * 1.48)
    ax.set_xlabel("Reports · colored bar = leading offense; gray remainder = all other offenses")
    ax.set_ylabel("Recorded coordinates (longitude, latitude)")
    ax.set_title("Which offense leads at the ten most frequently recorded locations?\nLabels show leading-type count / all reports at that coordinate", loc="left", pad=18)
    ax.legend(handles=[Patch(facecolor=color, label=label) for label, color in colors.items()],
              loc="lower right", frameon=True)
    ax.grid(axis="y", visible=False)
    sns.despine(ax=ax, left=True)
    save_chart(fig, "08_repeated_location_offenses.png")

    table = "\n".join(
        f"| {r.centerLong:.5f}, {r.centerLat:.5f} | {r.total_reports} | {r.leading_description} | {r.leading_count_per_type} ({r.leading_percent_per_type:.1f}%) |"
        for r in top.itertuples())
    report = f"""# Offense types at repeated coordinates

**Question:** Among the ten coordinate pairs with the most police reports in the local CSV, which offense description is most common at each pair?

Group `centerLong` and `centerLat` by exact equality, without rounding. A repeated location has at least two records. Rank locations by total reports, then compare all offense descriptions within each location. Ties are listed together; percentages refer to each tied type separately.

## Results

There are **{len(counts):,} distinct coordinate pairs**, including **{len(repeated):,} repeated pairs** containing **{result.total_reports.sum():,} reports ({100 * result.total_reports.sum() / len(df):.1f}% of the file)**. The ten largest locations contain {top.total_reports.sum():,} reports.

![Leading offense at the ten busiest recorded coordinate pairs](outputs/08_repeated_location_offenses.png)

| Longitude, latitude | Total reports | Leading description | Leading count (share) |
|---|---:|---|---:|
{table}

Shoplifting leads at four of these ten locations; other theft and theft from motor vehicles each lead at three. A leading category is the largest category, not necessarily a majority of reports.

## Interpretation and checks

- Exact equality means the same **recorded coordinates**, not proof of the same physical incident site. Public coordinates may be approximate or shared across nearby addresses. This analysis cannot establish why reports cluster there.
- Some coordinate pairs have multiple recorded neighborhood labels. Grouping by coordinates avoids assuming that one neighborhood label is correct; the [full summary](outputs/repeated_location_summary.csv) preserves every neighborhood label and its count.
- Use all records with valid coordinates, including those with missing neighborhood or UCR code. **{(~valid).sum()} records have missing/invalid coordinate ranges and are excluded.** Missing descriptions would be counted as Unknown offense. Dates cover January 1–October 21, 2026; these are counts, not risk estimates or complete-year totals.
- A separate `Counter` calculation reconciles all repeated-location report totals and the top ten leading-category counts. No source values are changed.

[Every repeated location and its leading type](outputs/repeated_location_summary.csv) · [All offense counts by repeated location](outputs/repeated_location_offense_counts.csv)

Run `.venv/bin/python analysis/repeated_locations.py` to regenerate.
"""
    (ROOT / "analysis/repeated_locations_summary.md").write_text(report)
    print(top[["centerLong", "centerLat", "total_reports", "leading_description", "leading_count_per_type"]].to_string(index=False))


if __name__ == "__main__":
    main()
