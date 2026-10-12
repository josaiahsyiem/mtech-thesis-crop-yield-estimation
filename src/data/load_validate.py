"""
Step 1: Load all yearly ground-truth shapefiles and validate consistency.
READ-ONLY. Does not change or write any data.

Run from project root (venv active):
    python src\\data\\load_validate.py
Expects the 4 shapefiles (with .dbf/.shx/.prj) in data\\raw\\.
"""
from pathlib import Path
import re
import geopandas as gpd
import pandas as pd

RAW_DIR = Path("data/raw")

CORE = ["UID", "Village", "Taluka", "Crop_Name", "Irrigation",
        "A_Variety", "C_Yeild", "HA_Date", "ASowing",
        "Carbon", "pH", "EC", "Nitrogen", "Phosphorus", "Potassium"]
ALT = {"Crop_Name": "Crop Name"}
AREA_ANY = ["Area_acres", "PolyArea", "PArea"]


def find_year(name):
    m = re.search(r"(20\d\d)", name)
    return m.group(1) if m else name


def has_col(cols, col):
    if col in cols:
        return True
    alt = ALT.get(col)
    return alt in cols if alt else False


def main():
    shp = sorted(RAW_DIR.glob("Latur_GT_ND_*.shp"))
    if not shp:
        print(f"NO shapefiles found in {RAW_DIR.resolve()}")
        print("Put the 4 full sets (.shp + .dbf + .shx + .prj) there and re-run.")
        return

    print(f"Found {len(shp)} shapefiles in {RAW_DIR.resolve()}\n")
    rows, crs_set = [], set()
    for p in shp:
        g = gpd.read_file(p)
        cols = set(g.columns)
        crs_set.add(str(g.crs))
        valid = g.geometry.notna()
        yv = pd.to_numeric(
            g["C_Yeild"], errors="coerce") if "C_Yeild" in cols else pd.Series(dtype=float)
        missing = [c for c in CORE if not has_col(cols, c)]
        rows.append({
            "year": find_year(p.name),
            "fields": len(g),
            "CRS": str(g.crs),
            "geom": ",".join(sorted(set(g.geom_type.dropna()))),
            "null_geom": int(g.geometry.isna().sum()),
            "invalid_geom": int((~g.loc[valid].geometry.is_valid).sum()),
            "yield_ok": int(yv.notna().sum()),
            "yield_bad": int(yv.isna().sum()),
            "area_col": next((c for c in AREA_ANY if c in cols), "NONE"),
            "missing_core": ",".join(missing) if missing else "none",
        })

    df = pd.DataFrame(rows).sort_values("year")
    pd.set_option("display.width", 200)
    print(df.to_string(index=False))

    print("\n=== CONSISTENCY CHECKS ===")
    if len(crs_set) == 1:
        print("All same CRS?  YES ->", next(iter(crs_set)))
    else:
        print("All same CRS?  NO  ->", crs_set)
    all_ok = all(r["missing_core"] == "none" for r in rows)
    print("All core columns present every year?  ",
          "YES" if all_ok else "NO (see missing_core)")
    print("Total fields:", df["fields"].sum(),
          "| total usable yield:", df["yield_ok"].sum())


if __name__ == "__main__":
    main()
