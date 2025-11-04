# roads_get_and_format

Gets all roads raw data from OSM and then combine all the segments using a sorting algorithm

## Quick Start - Unified District Creation

**NEW**: Use the unified `create_district_complete.py` program to create a complete district in one step!

This program condenses the entire district creation workflow into a single command:

```bash
# Interactive mode - will prompt for all inputs
python create_district_complete.py my_district.geojson

# Non-interactive mode with all parameters
python create_district_complete.py my_district.geojson \
  --name "North Hills" \
  --key north-hills \
  --creator-id 42 \
  --output my_district_upload.json
```

The unified program will:
1. ✓ Load the district border from GeoJSON (supports Polygon and MultiLineString)
2. ✓ Fetch or load road data from OpenStreetMap
3. ✓ Format and combine road segments
4. ✓ Load areas and sub-areas from folders
5. ✓ Assign areas/sub-areas to roads based on geographic intersection
6. ✓ Create a comprehensive upload payload ready for API submission

**Input Requirements:**
- `district_geojson`: Path to your district border GeoJSON file
- `--areas-folder`: Folder containing area GeoJSON files (default: `areas/`)
- `--sub-areas-folder`: Folder containing sub-area GeoJSON files (default: `sub_areas/`)

**User Inputs (interactive or via CLI):**
- District name (e.g., "North Hills")
- District key/slug (auto-generated if not provided)
- District status (default: "active")
- Creator user ID (optional)

**Output:**
- Complete district upload payload as JSON file (default: `district_upload_complete.json`)

See [Complete Usage Examples](#complete-district-creation-unified-program) for more details.

---

## Overview

This project consists of five Python programs:

1. **create_district_complete.py** ⭐ **NEW**: Unified program that handles the complete district creation workflow
2. **get_roads.py**: Extracts and formats all road data from OpenStreetMap within a district polygon, combining segments by road name
3. **add_areas.py**: Adds area and sub-area information to each road based on geographic intersection with polygons
4. **create_district.py**: Creates district objects matching database schema requirements for API upload or direct database insertion
5. **create_district_upload.py**: Creates comprehensive nested uploads with district, areas, roads, members, attachments, and events in a single transaction

## Installation

1. Clone the repository
2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Complete District Creation (Unified Program)

The easiest way to create a complete district is using the unified program:

```bash
# Interactive mode - will prompt for inputs
python create_district_complete.py my_district.geojson

# Non-interactive mode
python create_district_complete.py my_district.geojson \
  --name "My District" \
  --key my-district \
  --status active \
  --creator-id 42 \
  --areas-folder areas \
  --sub-areas-folder sub_areas \
  --output district_upload_complete.json
```

**Options:**
- `district_geojson`: Path to district border GeoJSON file (required)
- `--name NAME`: District name (will prompt if not provided)
- `--key KEY`: District key/slug (auto-generated from name if not provided)
- `--status STATUS`: District status - 'active', 'archived', or 'disabled' (default: 'active')
- `--creator-id ID`: Creator user ID (optional)
- `--areas-folder PATH`: Folder containing area GeoJSON files (default: 'areas')
- `--sub-areas-folder PATH`: Folder containing sub-area GeoJSON files (default: 'sub_areas')
- `--output FILE`: Output JSON file (default: 'district_upload_complete.json')
- `--online`: Fetch fresh data from OpenStreetMap (default: use cached data if available)
- `--roads-raw FILE`: Path to raw roads JSON file (default: 'roads_raw.json')

**Example Workflow:**

1. Prepare your district border GeoJSON file
2. (Optional) Create `areas/` folder with area GeoJSON files
3. (Optional) Create `sub_areas/` folder with sub-area GeoJSON files
4. Run the unified program
5. Upload the generated JSON file to your API

**Notes:**
- The program automatically converts MultiLineString (border paths) to Polygon
- Supports both interactive (prompts for inputs) and non-interactive (CLI args) modes
- Uses cached road data if available to avoid re-querying OpenStreetMap
- Automatically assigns areas and sub-areas to roads based on coordinate intersection

---

### Alternative: Step-by-Step Process

If you prefer to run each step separately, you can use the individual programs:

### Step 1: Extract and Format Roads from OSM

First, ensure you have a `my_district.geojson` file with a polygon defining your area of interest. A sample file is included.

Run the program to extract and format roads:

```bash
python get_roads.py
```

This will:
- Read the polygon from `my_district.geojson`
- Query OpenStreetMap for all roads within that polygon (or use existing `roads_raw.json` if available)
- Group road segments by road name
- Use a sorting algorithm to combine segments into continuous paths
- Save formatted roads to `roads_formatted.json`

**Offline Mode**: If `roads_raw.json` exists, the program automatically uses it instead of querying OpenStreetMap. Use `--online` flag to force fresh data from OSM.

**District ID**: Optionally specify a district ID to include in the output:
```bash
python get_roads.py --district-id=123
```

### Step 2: Add Area and Sub-Area Information

Run the program to add area and sub-area information to roads:

```bash
python add_areas.py
```

This will:
- Read formatted roads from `roads_formatted.json`
- Load all area polygons from the `areas/` folder (GeoJSON files)
- Load all sub-area polygons from the `sub_areas/` folder (GeoJSON files)
- For each area and sub-area, check every road to see if any coordinates fall within that polygon
- Add `areas` and `sub_areas` fields to each road containing lists of area/sub-area names
- Update `roads_formatted.json` in place with the area information

**Note**: A road can be in multiple areas or sub-areas if its coordinates span across different boundaries.

### Step 3: Create District Object

Run the program to create a district object:

```bash
python create_district.py
```

This will:
- Read the district polygon from `my_district.geojson`
- Generate a district object matching the database schema requirements
- Create both minimal (`district_minimal.json`) and full (`district_full.json`) district objects
- Validate all fields according to database constraints

The created district objects can be uploaded via API or inserted directly into a database.

**Command-line usage** (programmatic):
```python
from create_district import create_district_from_geojson, save_district_object

# Create a minimal district
district = create_district_from_geojson(
    'my_district.geojson',
    key='north-hills',
    name='North Hills',
    minimal=True
)

# Create a full district with all optional fields
full_district = create_district_from_geojson(
    'my_district.geojson',
    key='north-hills',
    name='North Hills',
    status='active',
    road_count=0,
    owner=42,
    created_by=42
)

# Save to file
save_district_object(full_district, 'my_district_object.json')
```

### Step 5: Create Comprehensive District Upload

For creating a complete district with all nested entities (areas, roads, members, attachments, events) in a single upload:

```bash
python create_district_upload.py
```

This will:
- Create a comprehensive upload payload with district, areas, roads, members, attachments, and events
- Use temporary IDs (temp_id) for client-side references before database IDs are assigned
- Support nested creation where roads reference areas, areas belong to district, etc.
- Generate `district_upload_comprehensive.json` ready for API upload

**Programmatic usage**:
```python
from create_district_upload import (
    create_area_object,
    create_road_object,
    create_district_member_object,
    create_comprehensive_upload
)
from create_district import create_district_from_geojson

# Create district
district = create_district_from_geojson(
    'my_district.geojson',
    key='north-hills',
    name='North Hills',
    status='active',
    owner=42,
    created_by=42
)

# Create areas with temporary IDs
areas = [
    create_area_object(
        temp_id="area-1",
        name="Sector A",
        area_border_coordinates={...},
        sub_area=0,
        created_by=42
    ),
    create_area_object(
        temp_id="area-1-1",
        name="Sector A - Sub 1",
        sub_area=1,
        created_by=42
    )
]

# Create roads that reference areas by temp_id
roads = [
    create_road_object(
        temp_id="road-1",
        key="main-st",
        name="Main Street",
        road_type="primary",
        length=1200.5,
        areas=["area-1"],  # Reference area by temp_id
        segments=[...],
        coordinates={...}
    )
]

# Create members
members = [
    create_district_member_object(
        user_id=42,
        role="admin",
        permissions=["manage_roads", "manage_areas"]
    )
]

# Create comprehensive upload
upload = create_comprehensive_upload(
    district=district,
    areas=areas,
    roads=roads,
    district_members=members
)

# Save to file or send to API
save_upload_payload(upload, 'my_upload.json')
```

## Output Formats

### Roads Output Format

The final output (`roads_formatted.json`) is a JSON object where:
- Keys are road names
- Values contain:
  - `name`: The road name
  - `district_id`: The district ID (optional, included if specified via --district-id flag)
  - `road_type`: The type of road (e.g., Street, Avenue, Boulevard, etc.), extracted from the road name. Null if no recognized type is found.
  - `coordinates`: List of road segments, where each segment is a list of [longitude, latitude] points. This allows drawing segments individually while keeping them together for the road.
  - `length`: Total length of the road in meters (sum of all segment lengths)
  - `size`: Size category based on road length - "big" (top 33% longest roads), "medium" (middle 33%), or "small" (bottom 33% shortest roads)
  - `segments`: Number of original segments combined (integer)
  - `areas`: List of area names that this road intersects (added by `add_areas.py`)
  - `sub_areas`: List of sub-area names that this road intersects (added by `add_areas.py`)

The `road_type` field is extracted by searching the road name from right to left for recognized road types:
Avenue, Bay, Boulevard, Circle, Court, Cove, Drive, Expressway, Lane, Parkway, Place, Road, Row, Spur, Street, and Way.

This ensures that roads like "Circle Road" are correctly identified as type "Road" (not "Circle"), and "Broadway Parkway" is identified as "Parkway" (not "Way").

The `size` field categorizes roads into three groups based on their length percentiles:
- **big**: Roads in the top 33% by length (the longest roads)
- **medium**: Roads in the middle 33% by length
- **small**: Roads in the bottom 33% by length (the shortest roads)

This categorization is useful for filtering or styling roads based on their relative importance in the road network.

### District Object Format

The district objects (`district_minimal.json` and `district_full.json`) follow the database schema requirements:

**Minimal district object** (required fields only):
```json
{
  "key": "north-hills",
  "name": "North Hills"
}
```

**Full district object** (all available fields):
```json
{
  "key": "north-hills",
  "name": "North Hills",
  "status": "active",
  "road_count": 0,
  "district_border_coordinates": {
    "type": "Polygon",
    "coordinates": [
      [
        [-122.4231, 37.8268],
        [-122.4231, 37.8168],
        [-122.4131, 37.8168],
        [-122.4131, 37.8268],
        [-122.4231, 37.8268]
      ]
    ]
  },
  "owner": 42,
  "created_by": 42
}
```

**District schema fields:**
- `id` (integer): DB-managed primary key. Not included in create payloads.
- `key` (string, required): Unique district slug (e.g., "north-hills")
- `name` (string, required): Human-readable district name
- `status` (string, optional): One of 'active', 'archived', 'disabled' (default: 'active')
- `road_count` (integer, optional): Number of roads in district (default: 0)
- `created_at` (ISO 8601 timestamp, optional): DB will set if omitted
- `created_by` (integer, optional): Foreign key to users.id
- `updated_at` (ISO 8601 timestamp, optional): DB trigger updates this
- `deleted_at` (ISO 8601 timestamp, optional): For soft-deletes
- `district_border_coordinates` (GeoJSON object, optional): Polygon or MultiPolygon in [lng, lat] format
- `owner` (integer, optional): Foreign key to users.id

**Validation rules:**
- `key`: non-empty, URL-safe slug format (lowercase, alphanumeric, hyphens), max 255 chars, unique
- `name`: non-empty, max 255 chars
- `status`: must be one of allowed values if provided
- `road_count`: non-negative integer
- `district_border_coordinates`: valid GeoJSON with closed polygon rings
- `owner`/`created_by`: must be integer user IDs if provided

### Comprehensive Upload Format

The comprehensive upload payload (`district_upload_comprehensive.json`) supports nested creation of district with all related entities in a single transaction. This format uses temporary IDs (temp_id) for client-side references before database IDs are assigned.

**Top-level structure:**
```json
{
  "district": {...},
  "areas": [...],
  "roads": [...],
  "district_members": [...],
  "attachments": [...],
  "events": [...]
}
```

**Area object fields:**
- `temp_id` (string, required): Client-side temporary ID for reference
- `name` (string, required): Human-readable area name
- `area_border_coordinates` (GeoJSON, optional): Polygon or MultiPolygon
- `status` (string, optional): 'active', 'archived', 'disabled'
- `sub_area` (integer, optional): 0 for regular area, 1 for sub-area
- `created_by` (integer, optional): Creator user ID

**Road object fields:**
- `temp_id` (string, required): Client-side temporary ID for reference
- `key` (string, required): Unique road slug
- `name` (string, required): Human-readable road name
- `type` (string, optional): Road type ('primary', 'secondary', 'residential', etc.)
- `length` (number, optional): Length in meters
- `size` (string, optional): 'small', 'medium', 'large'
- `segments` (array, optional): Array of segment objects with id, from, to, length_m
- `areas` (array, optional): Array of area temp_ids this road intersects
- `coordinates` (GeoJSON LineString, optional): Road geometry
- `sub_areas` (integer, optional): 0 or 1

**District member object fields:**
- `user_id` (integer, required): User ID
- `role` (string, optional): 'member', 'admin', 'editor', 'viewer'
- `permissions` (array, optional): List of permission strings
- `active` (integer, optional): 1 for active, 0 for inactive

**Attachment object fields:**
- `filename` (string, required): Filename
- `storage_key` (string, required): R2/S3 key or URL
- `content_type` (string, optional): MIME type
- `owner_id` (integer, optional): Owner user ID
- `size` (integer, optional): File size in bytes
- `organization_id` (integer, optional): Organization ID

**Event object fields:**
- `actor_id` (integer, optional): User ID who performed the action
- `object_type` (string, optional): 'district', 'area', 'road'
- `object_temp_id` (string, optional): Temporary ID reference
- `object_id` (integer, optional): Database ID
- `event_type` (string, optional): 'create', 'update', 'delete'
- `payload` (object, optional): Free-form JSON object

**Temporary ID references:**
- Roads can reference areas using temp_id values (e.g., `"areas": ["area-1", "area-2"]`)
- Server must resolve temp_ids to database IDs within the transaction
- All temp_ids must be unique within their entity type

**Transaction ordering:**
1. Insert district (obtain district_id)
2. Insert areas (map temp_id → area_id)
3. Insert roads (resolve area references, map temp_id → road_id)
4. Insert district_members
5. Insert attachments
6. Insert events

## Examples

### Roads Example

```json
{
  "Main Street": {
    "name": "Main Street",
    "district_id": 123,
    "road_type": "Street",
    "coordinates": [
      [
        [-122.4194, 37.7749],
        [-122.4184, 37.7759]
      ],
      [
        [-122.4184, 37.7759],
        [-122.4174, 37.7769]
      ],
      [
        [-122.4174, 37.7769],
        [-122.4164, 37.7779]
      ]
    ],
    "length": 567.8,
    "size": "big",
    "segments": 3,
    "areas": ["station-8", "station-9"],
    "sub_areas": []
  }
}
```

## How It Works

### Road Extraction and Formatting (get_roads.py)

Uses OSMnx library to:
1. Load the district polygon from GeoJSON
2. Query OpenStreetMap's Overpass API (or use existing roads_raw.json in offline mode)
3. Extract road network as a graph
4. Group segments by road name
5. Use a greedy sorting algorithm to combine segments into continuous paths
6. Calculate size categories based on road length percentiles
7. Output formatted roads with all required fields

The greedy sorting algorithm:
1. Groups segments by road name
2. Starts with first segment
3. Iteratively finds closest unconnected segment
4. Attaches segment to path (potentially reversing it)
5. Continues until all segments are combined

The algorithm ensures segments are spatially close, creating continuous road paths.

### Area and Sub-Area Assignment (add_areas.py)

Uses point-in-polygon checking to:
1. Load all area polygons from the `areas/` folder (GeoJSON files)
2. Load all sub-area polygons from the `sub_areas/` folder (GeoJSON files)
3. For each area and sub-area, iterate through all roads
4. Check if any coordinate of the road falls within the polygon
5. If a match is found, add the area/sub-area name to the road's `areas` or `sub_areas` list
6. Roads can belong to multiple areas or sub-areas if their coordinates span boundaries

The `areas/` and `sub_areas/` folders should contain GeoJSON files with Polygon geometries. Each filename (without extension) becomes the area or sub-area name in the output.

## Testing

The repository includes comprehensive test suites for all programs:

### Test the Unified Program

```bash
# Run unit tests for the unified program
python test_create_district_complete.py

# Test with sample data (non-interactive)
python create_district_complete.py my_district.geojson \
  --name "Test District" \
  --key test-district \
  --creator-id 42
```

### Test Individual Programs

```bash
# Test district creation
python test_create_district.py

# Test district upload payload creation
python test_district_upload.py

# Test area assignment
python test_add_areas.py

# Test road formatting
python test_format_roads.py

# Integration tests
python test_integration.py
```

The repository includes a sample `roads_raw.json` file with test data. You can test the programs directly using the included sample files.

**Note**: The `get_roads.py` and `create_district_complete.py` programs automatically use offline mode if `roads_raw.json` exists. They require internet access to query OpenStreetMap's Overpass API only when using the `--online` flag or when `roads_raw.json` doesn't exist.
