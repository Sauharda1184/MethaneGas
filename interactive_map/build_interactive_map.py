"""Build an interactive, pannable/zoomable HTML map of the US natural gas pipeline network.

Data source: Natural_Gas_Interstate_and_Intrastate_Pipelines shapefile (EPSG:3857).
Output: pipeline_map.html
"""

import geopandas as gpd
import folium

SHAPEFILE = "../Natural_Gas_Interstate_and_Intrastate_Pipelines/Natural_Gas_Interstate_and_Intrastate_Pipelines.shp"
OUTPUT = "pipeline_map.html"

COLORS = {"Interstate": "#d62728", "Intrastate": "#1f77b4"}


def main():
    gdf = gpd.read_file(SHAPEFILE)
    gdf = gdf[gdf.geometry.notna()]
    gdf = gdf.to_crs(epsg=4326)  # folium/Leaflet expects lat/lon

    center = [gdf.total_bounds[[1, 3]].mean(), gdf.total_bounds[[0, 2]].mean()]
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

    folium.LayerControl().add_to(m)
    m.save(OUTPUT)
    print(f"Saved {OUTPUT} ({len(gdf)} features plotted)")


if __name__ == "__main__":
    main()
