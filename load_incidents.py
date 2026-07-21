"""Load PHMSA gas transmission/gathering incident reports (2010-present) as a GeoDataFrame.

Source: gtggungs2010toPresent.xlsx (2010-present form; covers Gas Transmission,
Gas Gathering, and Underground Natural Gas Storage).

Earlier eras (gtgg2002to2009.xlsx, gtgg1986to2001.xlsx) are intentionally excluded:
2002-2009 coordinates are only ~37% geocodable (UTM/DMS transcription errors), and
1986-2001 has no coordinates at all.
"""

from pathlib import Path

import geopandas as gpd
import pandas as pd

DATA_DIR = Path(__file__).resolve().parent / "PHMSA_Pipeline_Safety_Flagged_Incidents"

LAT_RANGE = (15, 72)
LON_RANGE = (-180, -60)


def _clean_coords(lat, lon):
    lat = pd.to_numeric(lat, errors="coerce")
    lon = pd.to_numeric(lon, errors="coerce")

    # A handful of rows have the right magnitude but a missing negative sign on longitude.
    fixable = lat.between(*LAT_RANGE) & lon.between(-LON_RANGE[1], -LON_RANGE[0])
    lon = lon.where(~fixable, -lon)

    valid = lat.between(*LAT_RANGE) & lon.between(*LON_RANGE)
    return lat, lon, valid


def load_incidents(target_crs="EPSG:3857"):
    """Return 2010-present gas transmission/gathering incidents as points in target_crs."""
    df = pd.read_excel(DATA_DIR / "gtggungs2010toPresent.xlsx", sheet_name="gtggungs2010toPresent")
    lat, lon, valid = _clean_coords(df["LOCATION_LATITUDE"], df["LOCATION_LONGITUDE"])

    out = pd.DataFrame({
        "LATITUDE": lat,
        "LONGITUDE": lon,
        "INCIDENT_DATE": pd.to_datetime(df["LOCAL_DATETIME"], errors="coerce"),
        "IYEAR": df["IYEAR"],
        "SYSTEM_TYPE": df["SYSTEM_TYPE"],
        "OPERATOR": df["NAME"],
        "SIGNIFICANT": df["SIGNIFICANT"],
        "SERIOUS": df["SERIOUS"],
        "CAUSE": df["CAUSE"],
        "FATALITIES": df["FATAL"],
        "INJURIES": df["INJURE"],
        "TOTAL_COST_CURRENT": df["TOTAL_COST_CURRENT"],
        "IGNITED": df["IGNITE_IND"],
        "EXPLODED": df["EXPLODE_IND"],
        "GAS_RELEASED_MCF": df["GAS_FLOW_IN_PIPE_IN_MCF"],
    })
    out = out[valid]

    print(f"gtggungs2010toPresent: kept {valid.sum()} of {len(df)} rows "
          f"({(~valid).sum()} dropped for unusable coordinates)")

    gdf = gpd.GeoDataFrame(
        out,
        geometry=gpd.points_from_xy(out["LONGITUDE"], out["LATITUDE"]),
        crs="EPSG:4326",
    )
    return gdf.to_crs(target_crs)


if __name__ == "__main__":
    gdf = load_incidents()
    print(f"\nTotal incidents: {len(gdf)}")
    print(gdf["SYSTEM_TYPE"].value_counts())
