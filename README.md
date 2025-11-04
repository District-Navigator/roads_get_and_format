# roads_get_and_format

Gets all roads raw data from OSM and then combine all the segments using a sorting algorithm

## Overview

This project consists of five Python programs that work together to extract and format road data from OpenStreetMap and create district objects:

1. **get_roads.py**: Extracts all road segments within a polygon from OpenStreetMap
2. **format_roads.py**: Combines road segments by name using a sorting algorithm to create continuous paths
3. **add_areas.py**: Adds area information to each road based on geographic intersection with area polygons
4. **create_district.py**: Creates district objects matching database schema requirements for API upload or direct database insertion
5. **create_district_upload.py**: Creates comprehensive nested uploads with district, areas, roads, members, attachments, and events in a single transaction

## Installation

1. Clone the repository
2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Step 1: Extract Roads from OSM

First, ensure you have a `my_district.geojson` file with a polygon defining your area of interest. A sample file is included.

Run the first program to extract roads:

```bash
python get_roads.py
```

This will:
- Read the polygon from `my_district.geojson`
- Query OpenStreetMap for all roads within that polygon
- Save raw road segments to `roads_raw.json`

### Step 2: Format and Combine Roads

Run the second program to combine road segments:

```bash
python format_roads.py
```

This will:
- Read raw road segments from `roads_raw.json`
- Group segments by road name
- Use a sorting algorithm to combine segments into continuous paths
- Save formatted roads to `roads_formatted.json`

### Step 3: Add Area Information

Run the third program to add area information to roads:

```bash
python add_areas.py
```

This will:
- Read formatted roads from `roads_formatted.json`
- Load all area polygons from the `areas/` folder (GeoJSON files)
- For each area, check every road to see if any coordinates fall within that area
- Add an `areas` field to each road containing a list of area names
- Update `roads_formatted.json` in place with the area information

**Note**: A road can be in multiple areas if its coordinates span across different area boundaries.

### Step 4: Create District Object

Run the fourth program to create a district object:

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
  - `road_type`: The type of road (e.g., Street, Avenue, Boulevard, etc.), extracted from the road name. Null if no recognized type is found.
  - `coordinates`: List of road segments, where each segment is a list of [longitude, latitude] points. This allows drawing segments individually while keeping them together for the road.
  - `segment_count`: Number of original segments combined
  - `areas`: List of area names that this road intersects (added by `add_areas.py`)
  - `total_points`: Total coordinate points across all segments
  - `length`: Total length of the road in meters (sum of all segment lengths)
  - `size`: Size category based on road length - "big" (top 33% longest roads), "medium" (middle 33%), or "small" (bottom 33% shortest roads)

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
    "segment_count": 3,
    "total_points": 6,
    "length": 567.8,
    "size": "big",
    "areas": ["station-8", "station-9"]
  }
}
```

## How It Works

### Road Extraction (get_roads.py)

Uses OSMnx library to:
1. Load the district polygon from GeoJSON
2. Query OpenStreetMap's Overpass API
3. Extract road network as a graph
4. Convert to structured JSON format

### Road Formatting (format_roads.py)

Uses a greedy sorting algorithm to:
1. Group segments by road name
2. Start with first segment
3. Iteratively find closest unconnected segment
4. Attach segment to path (potentially reversing it)
5. Continue until all segments are combined

The algorithm ensures segments are spatially close, creating continuous road paths.

### Area Assignment (add_areas.py)

Uses point-in-polygon checking to:
1. Load all area polygons from the `areas/` folder (GeoJSON files)
2. For each area, iterate through all roads
3. Check if any coordinate of the road falls within the area polygon
4. If a match is found, add the area name to the road's `areas` list
5. Roads can belong to multiple areas if their coordinates span boundaries

The `areas/` folder should contain GeoJSON files with Polygon geometries. Each filename (without extension) becomes the area name in the output.

## Testing

The repository includes a sample `roads_raw.json` file with test data. You can test the formatting program directly:

```bash
python format_roads.py
```

This will process the sample data and create `roads_formatted.json`.

**Note**: The `get_roads.py` program requires internet access to query OpenStreetMap's Overpass API. If you're in a restricted network environment, you can use pre-generated `roads_raw.json` data or create your own sample data following the format shown in the sample file.
