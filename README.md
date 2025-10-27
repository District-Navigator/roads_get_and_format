# roads_get_and_format

Gets all roads raw data from OSM and then combine all the segments using a sorting algorithm

## Overview

This project consists of two Python programs that work together to extract and format road data from OpenStreetMap:

1. **get_roads.py**: Extracts all road segments within a polygon from OpenStreetMap
2. **format_roads.py**: Combines road segments by name using a sorting algorithm to create continuous paths

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

## Output Format

The final output (`roads_formatted.json`) is a JSON object where:
- Keys are road names
- Values contain:
  - `name`: The road name
  - `road_type`: The type of road (e.g., Street, Avenue, Boulevard, etc.), extracted from the road name. Null if no recognized type is found.
  - `coordinates`: List of road segments, where each segment is a list of [longitude, latitude] points. This allows drawing segments individually while keeping them together for the road.
  - `segment_count`: Number of original segments combined
  - `total_points`: Total coordinate points across all segments
  - `length`: Total length of the road in meters (sum of all segment lengths)

The `road_type` field is extracted by searching the road name from right to left for recognized road types:
Avenue, Bay, Boulevard, Circle, Court, Cove, Drive, Expressway, Lane, Parkway, Place, Road, Row, Spur, Street, and Way.

This ensures that roads like "Circle Road" are correctly identified as type "Road" (not "Circle"), and "Broadway Parkway" is identified as "Parkway" (not "Way").

## Example

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
    "length": 567.8
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

## Testing

The repository includes a sample `roads_raw.json` file with test data. You can test the formatting program directly:

```bash
python format_roads.py
```

This will process the sample data and create `roads_formatted.json`.

**Note**: The `get_roads.py` program requires internet access to query OpenStreetMap's Overpass API. If you're in a restricted network environment, you can use pre-generated `roads_raw.json` data or create your own sample data following the format shown in the sample file.
