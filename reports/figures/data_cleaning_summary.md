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
