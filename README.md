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

## Files

- `my_district.geojson` - Example GeoJSON file containing the Berea fire district boundary
- `schema.sql` - Database schema definition
- `roads.json` - Output file from step_2_get_roads.py (generated, not in repository)

## Requirements

- Python 3.x (no external dependencies required, uses only standard library)
