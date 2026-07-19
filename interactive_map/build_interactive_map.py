"""Build an interactive, pannable/zoomable HTML map of the US natural gas pipeline network.

Data source: Natural_Gas_Interstate_and_Intrastate_Pipelines shapefile (EPSG:3857).
Outputs:
  - pipeline_map.html            (pipelines only)
  - pipeline_incidents_map.html  (pipelines + PHMSA incidents, 2002-present)
"""

import sys
from pathlib import Path

import folium
import geopandas as gpd
import pandas as pd
from folium.plugins import MarkerCluster

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from load_incidents import load_incidents

SHAPEFILE = "../Natural_Gas_Interstate_and_Intrastate_Pipelines/Natural_Gas_Interstate_and_Intrastate_Pipelines.shp"
PIPELINE_ONLY_OUTPUT = "pipeline_map.html"
PIPELINE_INCIDENTS_OUTPUT = "pipeline_incidents_map.html"

COLORS = {"Interstate": "#d62728", "Intrastate": "#1f77b4"}
INCIDENT_COLOR = "#eb6834"


def build_pipeline_map(gdf, center):
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


def add_incidents(m, incidents):
    cluster = MarkerCluster(name="PHMSA incidents (2002-present)").add_to(m)
    for _, row in incidents.iterrows():
        date = row["INCIDENT_DATE"].date() if pd.notna(row["INCIDENT_DATE"]) else "unknown"
        popup = (
            f"<b>{row['OPERATOR']}</b><br>"
            f"Date: {date}<br>"
            f"System: {row['SYSTEM_TYPE']}<br>"
            f"Cause: {row['CAUSE']}<br>"
            f"Significant: {row['SIGNIFICANT']} &nbsp; Serious: {row['SERIOUS']}"
        )
        folium.CircleMarker(
            location=[row.geometry.y, row.geometry.x],
            radius=5,
            color=INCIDENT_COLOR,
            fill=True,
            fill_color=INCIDENT_COLOR,
            fill_opacity=0.7,
            weight=1,
            popup=folium.Popup(popup, max_width=250),
        ).add_to(cluster)


def main():
    gdf = gpd.read_file(SHAPEFILE)
    gdf = gdf[gdf.geometry.notna()]
    gdf = gdf.to_crs(epsg=4326)  # folium/Leaflet expects lat/lon
    center = [gdf.total_bounds[[1, 3]].mean(), gdf.total_bounds[[0, 2]].mean()]

    pipeline_only_map = build_pipeline_map(gdf, center)
    folium.LayerControl().add_to(pipeline_only_map)
    pipeline_only_map.save(PIPELINE_ONLY_OUTPUT)
    print(f"Saved {PIPELINE_ONLY_OUTPUT} ({len(gdf)} pipeline features)")

    incidents = load_incidents(target_crs="EPSG:4326")
    incidents_map = build_pipeline_map(gdf, center)
    add_incidents(incidents_map, incidents)
    folium.LayerControl().add_to(incidents_map)
    incidents_map.save(PIPELINE_INCIDENTS_OUTPUT)
    print(f"Saved {PIPELINE_INCIDENTS_OUTPUT} ({len(gdf)} pipeline features, {len(incidents)} incidents plotted)")


if __name__ == "__main__":
    main()
