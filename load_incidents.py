"""Combine PHMSA gas transmission/gathering incident reports (2002-present) into one GeoDataFrame.

Sources:
  - gtgg2002to2009.xlsx        (2002-2009 report form)
  - gtggungs2010toPresent.xlsx (2010-present form; adds Underground Natural Gas Storage)

The pre-2010 form's LATITUDE/LONGITUDE columns contain a mix of valid coordinates, UTM
eastings/northings, and malformed DMS fragments (likely transcription errors from paper/PDF
filings). Only values that parse as numbers and fall within a US-ish lat/lon range are kept;
the rest are dropped and counted. The 1986-2001 era has no coordinates at all and is not
included here.
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


def _load_2002_2009():
    df = pd.read_excel(DATA_DIR / "gtgg2002to2009.xlsx", sheet_name="gtgg2002to2009")
    lat, lon, valid = _clean_coords(df["LATITUDE"], df["LONGITUDE"])

    out = pd.DataFrame({
        "LATITUDE": lat,
        "LONGITUDE": lon,
        "INCIDENT_DATE": pd.to_datetime(df["IDATE"], errors="coerce"),
        "IYEAR": df["IYEAR"],
        "SYSTEM_TYPE": df["SYSTEM_TYPE"],
        "OPERATOR": df["NAME"],
        "SIGNIFICANT": df["SIGNIFICANT"],
        "SERIOUS": df["SERIOUS"],
        "CAUSE": df["CAUSE"],
        "FATALITIES": df["FATAL"],
        "INJURIES": df["INJURE"],
        "TOTAL_COST_CURRENT": df["TOTAL_COST_CURRENT"],
        "IGNITED": df["IGNITE"],
        "EXPLODED": df["EXPLO"],
        "GAS_RELEASED_MCF": pd.NA,
        "SOURCE_ERA": "2002-2009",
    })

    print(f"gtgg2002to2009: kept {valid.sum()} of {len(df)} rows "
          f"({(~valid).sum()} dropped for unusable coordinates)")
    return out[valid]


def _load_2010_present():
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
        "SOURCE_ERA": "2010-present",
    })

    print(f"gtggungs2010toPresent: kept {valid.sum()} of {len(df)} rows "
          f"({(~valid).sum()} dropped for unusable coordinates)")
    return out[valid]


def load_incidents(target_crs="EPSG:3857"):
    """Return all 2002-present gas transmission/gathering incidents as points in target_crs."""
    combined = pd.concat([_load_2002_2009(), _load_2010_present()], ignore_index=True)
    gdf = gpd.GeoDataFrame(
        combined,
        geometry=gpd.points_from_xy(combined["LONGITUDE"], combined["LATITUDE"]),
        crs="EPSG:4326",
    )
    return gdf.to_crs(target_crs)


if __name__ == "__main__":
    gdf = load_incidents()
    print(f"\nTotal combined incidents: {len(gdf)}")
    print(gdf["SOURCE_ERA"].value_counts())
    print(gdf["SYSTEM_TYPE"].value_counts())
