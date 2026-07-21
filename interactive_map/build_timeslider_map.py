"""Build an interactive map with a time slider showing PHMSA incidents (2010-present)
appearing over the pipeline network year by year.

Data sources:
  - Natural_Gas_Interstate_and_Intrastate_Pipelines shapefile (static base layer)
  - gtggungs2010toPresent.xlsx via load_incidents() (2010-present only; the 2002-2009
    file is excluded here since only ~37% of its coordinates are usable, which would
    make the year-by-year comparison misleading)

Output: pipeline_timeslider_map.html
"""

import sys
from pathlib import Path

import folium
import geopandas as gpd
import pandas as pd
from folium.plugins import TimestampedGeoJson

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from load_incidents import load_incidents

SHAPEFILE = "../Natural_Gas_Interstate_and_Intrastate_Pipelines/Natural_Gas_Interstate_and_Intrastate_Pipelines.shp"
OUTPUT = "pipeline_timeslider_map.html"

COLORS = {"Interstate": "#d62728", "Intrastate": "#1f77b4"}
INCIDENT_COLOR = "#eda100"


def build_base_map(gdf, center):
    m = folium.Map(location=center, zoom_start=4, tiles="cartodbpositron")
    for pipe_type, color in COLORS.items():
        layer = folium.FeatureGroup(name=pipe_type)
        subset = gdf[gdf["TYPEPIPE"] == pipe_type]
        folium.GeoJson(
            subset,
            style_function=lambda _, color=color: {"color": color, "weight": 1},
            tooltip=folium.GeoJsonTooltip(fields=["Operator", "TYPEPIPE", "Status"]),
        ).add_to(layer)
        layer.add_to(m)
    return m


def incidents_to_geojson_features(incidents):
    features = []
    for _, row in incidents.iterrows():
        popup = (
            f"<b>{row['OPERATOR']}</b><br>"
            f"Date: {row['INCIDENT_DATE'].date()}<br>"
            f"System: {row['SYSTEM_TYPE']}<br>"
            f"Cause: {row['CAUSE']}<br>"
            f"Significant: {row['SIGNIFICANT']} &nbsp; Serious: {row['SERIOUS']}"
        )
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [row.geometry.x, row.geometry.y]},
            "properties": {
                "time": row["INCIDENT_DATE"].strftime("%Y-%m-%d"),
                "popup": popup,
                "icon": "circle",
                "iconstyle": {
                    "fillColor": INCIDENT_COLOR,
                    "fillOpacity": 0.7,
                    "stroke": True,
                    "color": "black",
                    "weight": 1,
                    "radius": 6,
                },
            },
        })
    return features


def main():
    gdf = gpd.read_file(SHAPEFILE)
    gdf = gdf[gdf.geometry.notna()]
    gdf = gdf.to_crs(epsg=4326)
    center = [gdf.total_bounds[[1, 3]].mean(), gdf.total_bounds[[0, 2]].mean()]

    incidents = load_incidents(target_crs="EPSG:4326")

    m = build_base_map(gdf, center)

    TimestampedGeoJson(
        {"type": "FeatureCollection", "features": incidents_to_geojson_features(incidents)},
        period="P1Y",
        duration=None,  # points accumulate rather than disappear (cumulative build-up)
        transition_time=800,
        auto_play=False,
        loop=False,
        time_slider_drag_update=True,
        date_options="YYYY",
    ).add_to(m)

    folium.LayerControl().add_to(m)
    m.save(OUTPUT)
    print(f"Saved {OUTPUT} ({len(gdf)} pipeline features, {len(incidents)} incidents, "
          f"years {incidents['IYEAR'].min()}-{incidents['IYEAR'].max()})")


if __name__ == "__main__":
    main()
