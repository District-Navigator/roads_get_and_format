# Roads Get and Format

This repository contains scripts for working with district boundaries and road data from OpenStreetMap.

## Scripts

### Step 1: Create District SQL (`step_1_create_district_sql.py`)

Generates SQL INSERT queries for adding districts to the database, including boundary coordinates from a GeoJSON file.

**Usage:**
```bash
# Using default values from the script
python3 step_1_create_district_sql.py

# Using command-line arguments
python3 step_1_create_district_sql.py "District Name" 1 1

# Using a different GeoJSON file
python3 step_1_create_district_sql.py --geojson path/to/boundary.geojson
```

**Options:**
- `name` - District name (optional, defaults to value in script)
- `created_by` - User ID of the creator (optional, defaults to value in script)
- `owner` - User ID of the owner (optional, defaults to value in script)
- `--geojson` - Path to GeoJSON boundary file (default: my_district.geojson)

### Step 2: Get Roads from OpenStreetMap (`step_2_get_roads.py`)

Downloads all roads within the district boundary from OpenStreetMap using the Overpass API.

**Usage:**
```bash
# Download roads using default settings
python3 step_2_get_roads.py

# Specify custom GeoJSON boundary and output file
python3 step_2_get_roads.py --geojson my_district.geojson --output roads.json

# Use a different Overpass API endpoint
python3 step_2_get_roads.py --overpass-url https://overpass.kumi.systems/api/interpreter
```

**Options:**
- `--geojson` - Path to GeoJSON boundary file (default: my_district.geojson)
- `--output` - Path to output JSON file (default: roads.json)
- `--overpass-url` - Overpass API endpoint URL (default: https://overpass-api.de/api/interpreter)

**Note:** The Overpass API query may take some time depending on the size of the boundary and the number of roads. The default timeout is 180 seconds for the query and 300 seconds for the HTTP request.

### Step 3: Format Roads (`step_3_format_roads.py`)

Formats the roads data from step 2 into a structured format, grouping road segments by name and determining which areas/sub-areas each road is in. Unnamed roads are saved to a separate file for manual processing.

**Usage:**
```bash
# Format roads using default settings
python3 step_3_format_roads.py

# Specify custom input and output files
python3 step_3_format_roads.py --input roads.json --output formatted_roads.json

# Use custom areas and sub-areas directories
python3 step_3_format_roads.py --areas-dir areas --sub-areas-dir sub_areas

# Specify custom output file for unnamed roads
python3 step_3_format_roads.py --unnamed-output my_unnamed_roads.json
```

**Options:**
- `--input` - Path to input roads JSON file from step 2 (default: roads.json)
- `--output` - Path to output formatted JSON file (default: formatted_roads.json)
- `--areas-dir` - Path to directory containing area GeoJSON files (default: areas)
- `--sub-areas-dir` - Path to directory containing sub-area GeoJSON files (default: sub_areas)
- `--unnamed-output` - Path to output file for unnamed roads (default: unnamed_roads.json)

### Step 4: Create District SQL (`step_4_create_district_member_sql.py`)

Generates SQL INSERT queries for adding districts to the database, including boundary coordinates from a GeoJSON file.

**Usage:**
```bash
# Using default values from the script
python3 step_4_create_district_member_sql.py

# Using command-line arguments (all fields)
python3 step_4_create_district_member_sql.py "District Name" "2025-01-15 12:00:00" 1 1

# Using command-line arguments (minimal - name and user IDs only)
python3 step_4_create_district_member_sql.py "District Name" "" 1 1

# Using a different GeoJSON file
python3 step_4_create_district_member_sql.py --geojson path/to/boundary.geojson
```

**Options:**
- `name` - District name (optional, defaults to value in script)
- `created_at` - Created timestamp in ISO8601 format (optional, omit or use empty string for datetime('now'))
- `created_by` - User ID of the creator (optional, defaults to value in script)
- `owner` - User ID of the owner (optional, defaults to value in script)
- `--geojson` - Path to GeoJSON boundary file (default: my_district.geojson)

**Example Output:**
```sql
INSERT INTO districts (name, created_by, owner)
VALUES ('District Name', 1, 1);
```

**Output Format:**

The script produces two JSON files:

1. **Named roads** (default: `formatted_roads.json`) - Roads with names, grouped by name. Each road includes:
   - `name` - Full road name
   - `road_type` - Type extracted from name by searching right to left (e.g., "Circle Road" → "Road", "Fairwood Drive" → "Drive")
   - `coordinates` - Array of coordinate segments (each segment is an array of [lon, lat] pairs)
   - `length` - Total road length in meters
   - `segments` - Number of way segments that make up the road
   - `areas` - List of areas the road passes through
   - `sub_areas` - List of sub-areas the road passes through
   - `size` - Size category based on percentile distribution (small: bottom 33%, medium: middle 33%, large: top 33%)

2. **Unnamed roads** (default: `unnamed_roads.json`) - Road segments without names, saved as an array. Each segment includes:
   - `way_id` - OpenStreetMap way ID
   - `tags` - Original OSM tags for the way
   - `coordinates` - Array of [lon, lat] pairs for this segment

Example output structure:
```json
{
  "Fairwood Drive": {
    "name": "Fairwood Drive",
    "road_type": "Drive",
    "coordinates": [
      [[-82.452757, 34.924012], [-82.453003, 34.923821], ...]
    ],
    "length": 801.06,
    "segments": 8,
    "areas": ["station-9"],
    "sub_areas": [],
    "size": "medium"
  }
}
```

## Files

- `my_district.geojson` - Example GeoJSON file containing the Berea fire district boundary
- `schema.sql` - Database schema definition
- `roads.json` - Output file from step_2_get_roads.py (generated, not in repository)
- `formatted_roads.json` - Named roads output from step_3_format_roads.py (generated, not in repository)
- `unnamed_roads.json` - Unnamed roads output from step_3_format_roads.py (generated, not in repository)
- `areas/` - Directory containing area boundary GeoJSON files
- `sub_areas/` - Directory containing sub-area boundary GeoJSON files

## Requirements

- Python 3.x (no external dependencies required, uses only standard library)
