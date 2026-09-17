# Data Cleaning Summary: Latur Soybean Ground Truth

## What this covers
Cleaning of the field-level soybean ground truth data for the crop yield thesis.
Four kharif years from Latur district, Maharashtra: 2022, 2023, 2024, 2025.
Source: ground truth shapefiles.

## Result

| Year | Fields | Flagged | Saved file |
|------|--------|---------|------------|
| 2022 | 55 | 0 | clean_2022.gpkg |
| 2023 | 60 | 2 | clean_2023.gpkg |
| 2024 | 323 | 9 | clean_2024.gpkg |
| 2025 | 769 | 25 | clean_2025.gpkg |
| **Total** | **1,207** | **36** | in data/interim |

All four cleaned files share the same 23 columns and are saved as GeoPackage
(.gpkg) in data/interim. Raw files in data/raw are untouched.

## What was done to each year
1. Loaded the shapefile and inspected every column.
2. For 2022, 2023, 2024 (which were two batches merged), merged the doubled
   crop and area columns back into one each. Area in square meters was
   converted to acres (1 acre = 4046.86 m2).
3. Built a clean table keeping only useful columns, with simple lowercase
   names and a year column. Text yield and dates converted to real
   numbers and dates.
4. Dropped junk: private info (farmer, phone, agent), empty columns
   (Copper, Iron, Water pH, etc, all N/A), duplicate columns, and merge
   leftovers (layer, path, fid).
5. For 2025, repaired broken polygons with buffer(0).
6. Flagged wrong values in a qc_flag column. Marked, never deleted.

## Columns kept (23)
uid, year, taluka, village, crop, variety, irrigation, crop_yield,
sowing_date, harvest_date, area_acres, carbon, ph, ec, nitrogen,
phosphorus, potassium, soil_color, soil_structure, soil_texture,
soil_depth, geometry, qc_flag

## Key findings
- All 1,207 fields have a yield value. No missing targets.
- All four years are EPSG:4326, all soybean, all Latur district.
- The 1,207 fields are all distinct. No field repeats across years.
- Missing values are tiny once pooled: variety and sowing date about 2.8%,
  soil texture about 1.8%. All left as blanks for now.
- Soil description (color, texture, depth) is weak in 2022 (40% missing)
  and 2024 (63% missing), but full in 2023 and 2025. Keep or drop decision
  deferred to EDA.
- Village Harwadi (2025) has several bad polygons (negative area, broken
  geometry). 

## Flagged values (36 total, kept in files)
- yield_suspect: impossible or very high yields. Includes 720 and 260 in
  2023 (impossible), a 0 in 2025, and several high values 20 to 47 in 2024.
- bad_sowing_year: sowing date year does not match the file year (typos like
  1960, 1964, or wrong crop year). Yield is fine, only the date is wrong.
- area_suspect: zero or negative area (broken polygons).
- bad_geometry: empty or broken shapes that could not be repaired (2025).


---

## EDA findings (summary)

Full EDA is in notebooks/06_eda.ipynb. Key results:

- **Yield (target):** near-normal, mean 8.47, std 2.44 after removing the 36 flagged rows. Good for regression. Median yield is similar across 2022, 2023, 2025 (~8) and slightly higher in 2024 (~9.5).
- **Irrigation:** clearest categorical signal. Irrigated fields (Drip, Flow/Protective) median 9.0 vs Rainfed 8.0.
- **Soil chemistry (carbon, ph, ec, N, P, K):** ~80% placeholder-coded (-99 or 0). Not genuine measurements. Produced fake 1.00 correlations. Unusable.
- **Soil description (color, structure, texture, depth):** 81% real, weak but valid link to yield (best texture Black Cotton/Clay 8.5 vs Silt 7.74). Kept as minor features.
- **Variety:** 72 spellings mapping to ~12 real varieties. Needs standardization before use.
- **Spatial pattern:** fields form tight clusters; no strong regional yield gradient. Yield is driven by local field-level conditions, so per-field satellite features are the main signal source.
- **Spatial overlap:** about 90 plots overlap across years (heaviest 2024 vs 2025). Requires a spatial train/test split, not random.

## Fixes applied (analysis-ready dataset)

Applied in notebooks/07_apply_fixes.ipynb. Reads yield_master.gpkg, writes
yield_analysis_ready.gpkg. Master left untouched.

1. **Dropped soil chemistry columns** (carbon, ph, ec, nitrogen, phosphorus,
   potassium): ~80% placeholder, unusable.
2. **Dropped 3 impossible-yield fields** (720 and 260 in 2023, 0 in 2025):
   physically impossible, data provider could not confirm a unit error, so
   removed rather than imputed. High-but-real yields (20 to 47) were kept.
3. **Sowing dates with wrong year:** 15 were simple year typos with a valid
   kharif month (June/July), so the year was corrected to the field's crop
   year and the date kept. 2 (years 1960, 1964) had a suspicious month too,
   so were blanked.
4. **Recomputed area_acres** from the polygons in a projected CRS (UTM 43N).
   Fixed 7 negative areas. 1 field with an empty polygon has no area and will
   be dropped at the satellite step.

## Analysis-ready dataset

- File: data/processed/yield_analysis_ready.gpkg
- Rows: 1,204 (2022: 55, 2023: 58, 2024: 323, 2025: 768)
- Columns: 17 (uid, year, taluka, village, crop, variety, irrigation,
  crop_yield, sowing_date, harvest_date, area_acres, soil_color,
  soil_structure, soil_texture, soil_depth, qc_flag, geometry)

## Deferred to later stages (not done here)

- Filling missing values (variety, sowing_date, soil description): done inside
  the modelling pipeline on training data only, to avoid leakage.
- Variety name standardization: done in feature preparation.
- Broken/empty geometry (1 field): dropped at satellite extraction.
- Spatial train/test split: applied at modelling.
- Final decision on the dropped 720/260: currently excluded; revisit if the
  data provider confirms units.