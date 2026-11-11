"""Plot ten Downtown West records in WGS84: X=longitude, Y=latitude."""

from html import escape
import math

from explore_police import ROOT, OUT, save_chart
import folium
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.ticker import FormatStrFormatter
import pandas as pd
import seaborn as sns


def main():
    df = pd.read_csv(ROOT / "data/Police_Incidents_2026.csv", dtype={"caseNumber": "string"})
    # Deterministic convenience sample, not a random or representative sample.
    sample = df.loc[df.neighborhood.eq("Downtown West")].sort_values("OBJECTID").head(10).copy()
    sample.insert(0, "sample_id", range(1, len(sample) + 1))
    if sample[["centerLong", "centerLat"]].isna().any().any():
        raise ValueError("Sample contains missing coordinates; inspect before plotting.")
    # Assign the user's requested CRS to existing degree coordinates. This is
    # not a coordinate transformation, geocoding step, or use of CSV X/Y fields.
    points = gpd.GeoDataFrame(sample, geometry=gpd.points_from_xy(
        sample.centerLong, sample.centerLat), crs="EPSG:4326")
    boundaries = gpd.read_file(ROOT / "data/minneapolis_neighborhoods.geojson").to_crs(4326)
    boundary = boundaries.loc[boundaries.BDNAME.eq("Downtown West")]
    polygon = boundary.geometry.iloc[0]
    points["inside_downtown_west_boundary"] = points.geometry.map(polygon.covers)
    assert points.crs.to_epsg() == 4326
    assert (points.geometry.x == points.centerLong).all()
    assert (points.geometry.y == points.centerLat).all()

    columns = ["sample_id", "caseNumber", "neighborhood", "centerLong", "centerLat", "inside_downtown_west_boundary"]
    points[columns].to_csv(OUT / "downtown_west_coordinate_sample.csv", index=False, float_format="%.5f")
    points[columns + ["geometry"]].to_file(OUT / "downtown_west_coordinate_sample.geojson", driver="GeoJSON")
    grouped = points.groupby(["centerLong", "centerLat"], sort=False)

    sns.set_theme(style="whitegrid", rc={"axes.titleweight": "bold", "figure.constrained_layout.use": True})
    fig, axes = plt.subplots(1, 2, figsize=(13, 7))
    minx, miny, maxx, maxy = boundary.total_bounds
    for ax in axes:
        boundary.plot(ax=ax, facecolor="#EBF2F4", edgecolor="#347A92", linewidth=1.3)
        for (lon, lat), rows in grouped:
            inside = rows.inside_downtown_west_boundary.all()
            ax.scatter(lon, lat, s=65, color="#347A92" if inside else "#D58047", zorder=3)
            ax.annotate(", ".join(rows.sample_id.astype(str)), (lon, lat),
                        xytext=(6, 6), textcoords="offset points", fontsize=9,
                        bbox={"facecolor": "white", "alpha": 0.85, "edgecolor": "none", "pad": 1}, zorder=4)
        ax.set_xlabel("X = centerLong · longitude (degrees)")
        ax.set_ylabel("Y = centerLat · latitude (degrees)")
        ax.xaxis.set_major_formatter(FormatStrFormatter("%.3f"))
        ax.yaxis.set_major_formatter(FormatStrFormatter("%.3f"))
        ax.tick_params(axis="x", labelrotation=30)
        ax.set_aspect(1 / math.cos(math.radians(points.centerLat.mean())))
    axes[0].set_title("All 10 records · original coordinates", loc="left")
    axes[0].margins(0.15)
    axes[1].set_xlim(minx - 0.001, maxx + 0.001)
    axes[1].set_ylim(miny - 0.001, maxy + 0.001)
    axes[1].set_title("Downtown West zoom · boundary shown", loc="left")
    fig.suptitle("Downtown West sample | WGS84 (EPSG:4326)\nLabels are sample IDs; shared coordinates retain all IDs. Orange = outside boundary.", fontsize=13)
    save_chart(fig, "07_downtown_west_coordinate_sample.png")

    view = folium.Map(location=[44.97, -93.27], tiles="OpenStreetMap", zoom_start=13)
    folium.GeoJson(boundary[["BDNAME", "geometry"]], name="Downtown West boundary",
                   style_function=lambda f: {"color": "#347A92", "weight": 2, "fillOpacity": 0.08}).add_to(view)
    for (lon, lat), rows in grouped:
        ids = ", ".join(rows.sample_id.astype(str))
        cases = "<br>".join(escape(c) for c in rows.caseNumber)
        inside = bool(rows.inside_downtown_west_boundary.all())
        folium.Marker(
            location=[lat, lon],  # Folium's display API takes latitude first.
            tooltip=f"Sample {ids}",
            popup=folium.Popup(f"<b>Sample {ids}</b><br>{cases}<br>Recorded neighborhood: Downtown West"
                               f"<br>Longitude (X): {lon:.5f}<br>Latitude (Y): {lat:.5f}"
                               f"<br>Inside downloaded boundary: {inside}", max_width=340),
            icon=folium.Icon(color="blue" if inside else "orange", icon="info-sign"),
        ).add_to(view)
    view.fit_bounds([[points.centerLat.min() - .002, points.centerLong.min() - .002],
                     [max(maxy, points.centerLat.max()) + .002, max(maxx, points.centerLong.max()) + .002]])
    view.save(OUT / "downtown_west_coordinate_sample.html")

    table_rows = "\n".join(
        f"| {r.sample_id} | {r.caseNumber} | {r.neighborhood} | {r.centerLong:.5f} | {r.centerLat:.5f} | {'Yes' if r.inside_downtown_west_boundary else 'No'} |"
        for r in points.itertuples())
    outside = points.loc[~points.inside_downtown_west_boundary]
    report = f"""# Downtown West: ten coordinate examples

Select the first ten rows labeled `Downtown West`, ordered by `OBJECTID`. This is a reproducible convenience sample, not a representative sample.

**X = `centerLong` (longitude); Y = `centerLat` (latitude).** The existing degree values are assigned **WGS84 / EPSG:4326** without converting to meters or using the CSV's separate `X`/`Y` columns. This assignment follows the requested interpretation; it does not independently establish the source datum.

![Ten coordinate examples and downtown zoom](outputs/07_downtown_west_coordinate_sample.png)

[Interactive map](outputs/downtown_west_coordinate_sample.html) · [CSV table](outputs/downtown_west_coordinate_sample.csv) · [WGS84 GeoJSON](outputs/downtown_west_coordinate_sample.geojson)

| Sample ID | Case number | Recorded neighborhood | Longitude (X) | Latitude (Y) | Inside boundary? |
|---|---|---|---:|---:|---|
{table_rows}

**What the sample reveals:** ten records occupy {len(grouped)} distinct coordinate pairs. Shared locations are not moved or jittered; their labels list every sample ID. **{len(outside)} record is outside the downloaded Downtown West boundary**, despite its recorded neighborhood label. The orange point retains its original coordinates and neighborhood; neither is corrected or excluded. The map alone cannot establish whether the coordinate or neighborhood label is wrong. The zoom panel shows the downtown cluster; the overview includes every sampled point.

The boundary check uses the city's cached neighborhood polygon, including its edges (`covers`). It is a geographic consistency check, not independent verification of the exact incident site. Folium accepts `[latitude, longitude]` for markers; GeoJSON and the static plot use X/Y = longitude/latitude.

Run `.venv/bin/python analysis/map_coordinate_sample.py` to regenerate. No records in the input CSV are changed.
"""
    (ROOT / "analysis/coordinate_sample.md").write_text(report)
    print(points[columns].to_string(index=False))


if __name__ == "__main__":
    main()
