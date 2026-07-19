"""Render the US natural gas interstate/intrastate pipeline network as a static map.

Data source: Natural_Gas_Interstate_and_Intrastate_Pipelines shapefile (EPSG:3857).
Output: pipeline_map.png
"""

import geopandas as gpd
import matplotlib.pyplot as plt
import contextily as cx

SHAPEFILE = "Natural_Gas_Interstate_and_Intrastate_Pipelines/Natural_Gas_Interstate_and_Intrastate_Pipelines.shp"
OUTPUT = "pipeline_map.png"

COLORS = {"Interstate": "#d62728", "Intrastate": "#1f77b4"}


def main():
    gdf = gpd.read_file(SHAPEFILE)
    gdf = gdf[gdf.geometry.notna()]

    fig, ax = plt.subplots(figsize=(14, 9))

    for pipe_type, color in COLORS.items():
        subset = gdf[gdf["TYPEPIPE"] == pipe_type]
        subset.plot(ax=ax, color=color, linewidth=0.4, label=pipe_type)

    cx.add_basemap(ax, crs=gdf.crs, source=cx.providers.CartoDB.Positron)

    ax.set_axis_off()
    ax.set_title("US Natural Gas Interstate and Intrastate Pipelines", fontsize=14)
    ax.legend(loc="lower right", fontsize=10, frameon=True)

    fig.tight_layout()
    fig.savefig(OUTPUT, dpi=200)
    print(f"Saved {OUTPUT} ({len(gdf)} features plotted)")


if __name__ == "__main__":
    main()
