"""Render the US natural gas interstate/intrastate pipeline network as a static map.

Data source: Natural_Gas_Interstate_and_Intrastate_Pipelines shapefile (EPSG:3857).
Outputs:
  - pipeline_map.png            (pipelines only)
  - pipeline_incidents_map.png  (pipelines + PHMSA incidents, 2002-present)
"""

import geopandas as gpd
import matplotlib.pyplot as plt
import contextily as cx

from load_incidents import load_incidents

SHAPEFILE = "Natural_Gas_Interstate_and_Intrastate_Pipelines/Natural_Gas_Interstate_and_Intrastate_Pipelines.shp"
PIPELINE_ONLY_OUTPUT = "pipeline_map.png"
PIPELINE_INCIDENTS_OUTPUT = "pipeline_incidents_map.png"

COLORS = {"Interstate": "#d62728", "Intrastate": "#1f77b4"}
INCIDENT_COLOR = "#eb6834"


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

    fig.savefig(PIPELINE_ONLY_OUTPUT, dpi=200)
    print(f"Saved {PIPELINE_ONLY_OUTPUT} ({len(gdf)} features plotted)")

    # Freeze the extent so adding incident points below doesn't autoscale the
    # axes past the basemap tiles already fetched for that extent.
    xlim, ylim = ax.get_xlim(), ax.get_ylim()

    incidents = load_incidents(target_crs=gdf.crs)
    incidents.plot(
        ax=ax, color=INCIDENT_COLOR, markersize=8, alpha=0.6,
        edgecolor="black", linewidth=0.2, zorder=4,
        label="PHMSA incident (2002-present)",
    )
    ax.set_xlim(xlim)
    ax.set_ylim(ylim)
    ax.legend(loc="lower right", fontsize=10, frameon=True)

    fig.savefig(PIPELINE_INCIDENTS_OUTPUT, dpi=200)
    print(f"Saved {PIPELINE_INCIDENTS_OUTPUT} ({len(gdf)} pipeline features, {len(incidents)} incidents plotted)")


if __name__ == "__main__":
    main()
