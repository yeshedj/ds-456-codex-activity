"""Map the local CSV using cached city boundaries; no network needed to rerun."""

from pathlib import Path
from collections import Counter
from datetime import datetime, timezone
import json

# Set the existing plotting/cache configuration before importing map libraries.
from explore_police import ROOT, OUT, save_chart

import geopandas as gpd
import folium
from folium.plugins import HeatMap
from branca.colormap import linear
import pandas as pd
import seaborn as sns

import matplotlib.pyplot as plt

BOUNDARY_SOURCE = "https://services.arcgis.com/afSMGVsC7QlRK1kZ/arcgis/rest/services/Minneapolis_Neighborhoods/FeatureServer/0"


def main():
    df = pd.read_csv(ROOT / "data/Police_Incidents_2026.csv", dtype={"caseNumber": "string"})
    boundaries = gpd.read_file(ROOT / "data/minneapolis_neighborhoods.geojson").to_crs(4326)
    if boundaries.BDNAME.duplicated().any():
        raise ValueError("Boundary names must be unique before joining.")
    named = df.loc[df.neighborhood.notna()].copy()
    named["description"] = named.description.fillna("Unknown offense")
    unmatched = sorted(set(named.neighborhood) - set(boundaries.BDNAME))
    if unmatched:
        raise ValueError(f"Resolve unmatched neighborhood names before mapping: {unmatched}")

    # Use the CSV's recorded neighborhood; coordinates are only for the optional
    # density layer. No address geocoding or inferred neighborhood assignments.
    counts = pd.crosstab(named.neighborhood, named.description)
    totals = counts.sum(axis=1).sort_values(ascending=False)
    maximum = counts.max(axis=1)
    dominant = counts.apply(lambda row: " / ".join(row.index[row.eq(row.max())]), axis=1)
    summary = pd.DataFrame({
        "total_records": totals,
        "leading_description": dominant,
        "leading_count": maximum,
        "leading_percent": (100 * maximum / totals).round(1),
    }).sort_values("total_records", ascending=False).rename_axis("neighborhood")
    summary.to_csv(OUT / "neighborhood_map_summary.csv")
    counts.to_csv(OUT / "neighborhood_offense_counts.csv")
    grouped = boundaries.merge(summary, left_on="BDNAME", right_index=True, how="left", validate="one_to_one")
    grouped["total_records"] = grouped.total_records.fillna(0).astype(int)
    grouped["leading_description"] = grouped.leading_description.fillna("No records")
    grouped["leading_count"] = grouped.leading_count.fillna(0).astype(int)
    grouped["leading_percent"] = grouped.leading_percent.fillna(0)
    assert grouped.total_records.sum() + df.neighborhood.isna().sum() == len(df)

    # Independent count reconciliation using Python's Counter, not groupby.
    independent = Counter(df.neighborhood.dropna())
    assert dict(totals) == dict(independent)
    for neighborhood in totals.head(5).index:
        categories = Counter(df.loc[df.neighborhood.eq(neighborhood), "description"])
        assert max(categories.values()) == int(summary.loc[neighborhood, "leading_count"])

    sns.set_theme(style="white", font_scale=1.0, rc={
        "axes.titleweight": "bold", "text.color": "#25344A",
        "figure.constrained_layout.use": True,
    })
    # A projected CRS keeps the static map's neighborhood shapes proportional.
    projected = grouped.to_crs(26915)
    fig, (map_ax, rank_ax) = plt.subplots(1, 2, figsize=(13, 10), gridspec_kw={"width_ratios": [1.25, 1]})
    projected.plot(column="total_records", cmap="YlOrRd", edgecolor="white", linewidth=0.55,
                   legend=True, legend_kwds={"label": "Recorded incidents", "shrink": 0.55}, ax=map_ax)
    for rank, name in enumerate(totals.head(5).index, 1):
        point = projected.loc[projected.BDNAME.eq(name)].geometry.iloc[0].representative_point()
        map_ax.text(point.x, point.y, str(rank), ha="center", va="center", fontsize=10,
                    bbox={"boxstyle": "circle,pad=0.25", "fc": "white", "ec": "#344256"})
    map_ax.set_axis_off()
    map_ax.set_title("More reports = darker shading", loc="left", pad=16)
    top = totals.head(10)
    sns.barplot(x=top.values, y=[f"{i}. {name}" for i, name in enumerate(top.index, 1)],
                color="#347A92", errorbar=None, ax=rank_ax)
    rank_ax.bar_label(rank_ax.containers[0], labels=[f"{n:,}" for n in top], padding=4)
    rank_ax.set_xlim(0, top.max() * 1.2)
    rank_ax.set_xlabel("Recorded incidents")
    rank_ax.set_title("Neighborhoods with the most records", loc="left", pad=16)
    sns.despine(ax=rank_ax, left=True)
    fig.suptitle("Minneapolis police reports | Jan 1–Oct 21, 2026\nCounts by recorded neighborhood; not population-adjusted rates", fontsize=16)
    save_chart(fig, "05_neighborhood_map.png")

    # Keep all incident types in each displayed row: combine the remaining
    # descriptions into Other categories, so row sums still equal total counts.
    top_types = counts.sum().nlargest(8).index
    matrix = counts.loc[totals.head(20).index, top_types].copy()
    matrix["Other categories"] = totals.loc[matrix.index] - matrix.sum(axis=1)
    fig, ax = plt.subplots(figsize=(14, 10))
    sns.heatmap(matrix, cmap="YlOrRd", annot=True, fmt=",d", linewidths=0.5,
                cbar_kws={"label": "Recorded incidents"}, ax=ax)
    ax.set_title("Which incident types are most common?\n20 neighborhoods with the most records · eight largest citywide categories + remainder", loc="left", pad=20)
    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.set_xticklabels(ax.get_xticklabels(), rotation=35, ha="right", fontsize=9)
    save_chart(fig, "06_neighborhood_offense_heatmap.png")

    map_view = folium.Map(location=[44.975, -93.265], zoom_start=11, tiles="OpenStreetMap")
    color = linear.YlOrRd_09.scale(0, int(totals.max()))
    color.caption = "Recorded incidents per neighborhood (not a rate)"
    color.add_to(map_view)
    folium.GeoJson(
        grouped[["BDNAME", "total_records", "leading_description", "leading_count", "leading_percent", "geometry"]],
        name="Neighborhood incident totals", show=True,
        style_function=lambda feature: {
            "fillColor": color(feature["properties"]["total_records"]),
            "color": "#66717c", "weight": 0.6, "fillOpacity": 0.75,
        },
        highlight_function=lambda feature: {"weight": 2, "color": "#25344A"},
        tooltip=folium.GeoJsonTooltip(
            fields=["BDNAME", "total_records", "leading_description", "leading_count", "leading_percent"],
            aliases=["Neighborhood", "Total incidents", "Most common type (ties listed)", "Count per leading type", "Share per leading type (%)"],
            localize=True,
        ),
    ).add_to(map_view)

    # Same named-neighborhood subset as the choropleth. Coordinates are supplied
    # to Leaflet in latitude/longitude order, never projected X/Y or IDs.
    lon = pd.to_numeric(named.centerLong, errors="coerce")
    lat = pd.to_numeric(named.centerLat, errors="coerce")
    valid_coords = lon.between(-180, 180) & lat.between(-90, 90) & ~(lon.eq(0) & lat.eq(0))
    points = pd.DataFrame({"lat": lat[valid_coords], "lon": lon[valid_coords]})
    weighted = points.groupby(["lat", "lon"]).size().reset_index(name="records")
    # Leaflet expects relative weights in [0, 1]; preserve count proportions.
    weighted["weight"] = weighted.records / weighted.records.max()
    density_layer = folium.FeatureGroup(name="Point density (hide totals layer to view)", show=False)
    HeatMap(weighted[["lat", "lon", "weight"]].values.tolist(), radius=18, blur=15,
            min_opacity=0.2, max_zoom=15).add_to(density_layer)
    density_layer.add_to(map_view)
    folium.LayerControl(collapsed=False).add_to(map_view)
    map_view.get_root().html.add_child(folium.Element(
        '<div style="position:fixed;bottom:20px;left:15px;z-index:9999;background:white;'
        'padding:12px;border:1px solid #ccc;max-width:320px;font:14px Arial">'
        '<b>Police reports: Jan 1–Oct 21, 2026</b><br>Hover for totals and leading incident type.'
        '<br>11 records with no neighborhood excluded. Counts are not risk estimates.'
        '<br>Point density is smoothed and changes with zoom; its colors do not use the count legend.</div>'
    ))
    map_view.save(OUT / "neighborhood_incidents_interactive.html")

    audit = {
        "total_csv_records": len(df), "mapped_records": int(totals.sum()),
        "missing_neighborhood_records": int(df.neighborhood.isna().sum()),
        "boundary_neighborhoods": len(boundaries), "unmatched_names": unmatched,
        "density_records": int(valid_coords.sum()),
        "invalid_coordinates_in_named_records": int((~valid_coords).sum()),
        "independent_counter_check": "passed for every neighborhood total and top-five leading counts",
        "boundary_source": BOUNDARY_SOURCE,
    }
    (OUT / "mapping_checks.json").write_text(json.dumps(audit, indent=2))
    provenance = ROOT / "data/minneapolis_neighborhoods_source.json"
    if not provenance.exists():
        provenance.write_text(json.dumps({"source": BOUNDARY_SOURCE,
            "query": "where=1=1&outFields=*&outSR=4326&f=geojson",
            "retrieved_utc": datetime.now(timezone.utc).isoformat(),
            "features": len(boundaries), "crs": "EPSG:4326"}, indent=2))
    rows = "\n".join(f"| {name} | {row.total_records:,} | {row.leading_description} | {row.leading_count:,} ({row.leading_percent:.1f}%) |"
                     for name, row in summary.head(5).iterrows())
    report = f"""# Neighborhood incident maps

[Open the interactive map](outputs/neighborhood_incidents_interactive.html). Hover over a neighborhood for its total and leading incident type. Use the layer controls to turn off neighborhood totals and turn on **Point density** for a smoothed heatmap. The HTML needs internet access for map tiles and JavaScript libraries; PNGs below work offline.

## Where are the most incidents recorded?

![Neighborhood totals and ranking](outputs/05_neighborhood_map.png)

Darker areas have more records. Numbered markers identify the five neighborhoods at the top of the ranking.

| Neighborhood | All records | Most common description | Leading count (share) |
|---|---:|---|---:|
{rows}

## Which types are most common within neighborhoods?

![Incident types by neighborhood](outputs/06_neighborhood_offense_heatmap.png)

Rows are the 20 neighborhoods with the most records, ordered by total. Columns show the eight largest citywide descriptions plus **Other categories**, which combines all remaining descriptions. Cell numbers and colors show counts; row totals include every description. The combined Other column should not be interpreted as a single incident type. The map hover and [full neighborhood summary](outputs/neighborhood_map_summary.csv) identify each neighborhood's actual leading description across all categories, including ties.

## How the mapping works

- Join CSV `neighborhood` to `BDNAME` in the [City of Minneapolis boundary layer]({BOUNDARY_SOURCE}). All **87 named neighborhoods match exactly**; no fuzzy matching or geocoding is used.
- Map **{int(totals.sum()):,} records**. The **{df.neighborhood.isna().sum()} records without a neighborhood** remain in the original data and the exploration's Unknown group; they are excluded from neighborhood maps and the density layer. Missing `UCRCode` and `centergbsid` do not exclude records.
- GeoJSON boundaries use longitude/latitude (EPSG:4326). The static map is projected to NAD83 / UTM zone 15N (EPSG:26915). The density layer uses `centerLat`/`centerLong`; repeated locations are weighted by their record counts. All {int(valid_coords.sum()):,} mapped records have valid coordinate ranges. Public locations are approximate, and density colors are relative concentrations, not exact counts or geographic risk.
- These maps use the CSV's **recorded neighborhood**, not a new point-in-polygon assignment. Counts are police records, not all incidents or population-adjusted rates. Coverage is January 1–October 21, 2026.

## Checks and reuse

All neighborhood totals were independently recomputed with Python's `Counter` and match the plotted totals. Leading-type counts for the five largest neighborhoods also match. **{int(totals.sum()):,} mapped + {df.neighborhood.isna().sum()} unknown = {len(df):,} original records**; no join duplicated rows. See [checks](outputs/mapping_checks.json) and [all neighborhood/type counts](outputs/neighborhood_offense_counts.csv).

Run `.venv/bin/python analysis/map_police.py` to rebuild from the cached boundary file. Boundary source and retrieval details are saved under `data/`.
"""
    (ROOT / "analysis/mapping_summary.md").write_text(report)
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
