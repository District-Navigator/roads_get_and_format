#!/usr/bin/env python3
"""
Program 1: Get and Format Roads from District Border
Extracts all road data from OpenStreetMap within a polygon defined in my_district.geojson,
combines segments by road name, and outputs formatted roads with district_id support.
"""

import json
import math
import geopandas as gpd
import osmnx as ox
from shapely.geometry import shape
from collections import defaultdict

# List of valid road types for extraction
ROAD_TYPES = [
    'Avenue', 'Bay', 'Boulevard', 'Circle', 'Court', 'Cove', 'Drive',
    'Expressway', 'Lane', 'Parkway', 'Place', 'Road', 'Row', 'Spur',
    'Street', 'Way'
]


def load_district_polygon(geojson_file):
    """
    Load the district polygon from a GeoJSON file.
    
    Args:
        geojson_file: Path to the GeoJSON file containing the district polygon
        
    Returns:
        shapely.geometry.Polygon: The district boundary polygon
    """
    with open(geojson_file, 'r') as f:
        geojson_data = json.load(f)
    
    # Extract the first feature's geometry
    if geojson_data['type'] == 'FeatureCollection':
        geometry = geojson_data['features'][0]['geometry']
    else:
        geometry = geojson_data['geometry']
    
    polygon = shape(geometry)
    return polygon


def get_roads_from_polygon(polygon):
    """
    Fetch all roads within the given polygon from OpenStreetMap.
    
    Args:
        polygon: shapely.geometry.Polygon defining the area
        
    Returns:
        networkx.MultiDiGraph: Road network graph
    """
    # Get the street network within the polygon
    # Using 'drive' network type to get all drivable roads
    G = ox.graph_from_polygon(polygon, network_type='drive')
    return G


def normalize_road_name(name):
    """
    Normalize a road name that may be a string or list.
    
    Args:
        name: Road name (string, list, or other)
        
    Returns:
        str: Normalized road name as a string
    """
    if isinstance(name, list):
        # Join multiple names with " / " separator
        normalized = ' / '.join(str(n) for n in name if n)
        return normalized if normalized else 'Unknown'
    return name if name else 'Unknown'


def extract_road_type(road_name):
    """
    Extract the road type from a road name by searching right-to-left.
    
    Searches for road type suffixes (Avenue, Boulevard, Street, etc.) from
    right to left to avoid false matches. For example, "Circle Road" should
    return "Road" not "Circle", and "Parkway" should not match "Way".
    
    Args:
        road_name: The full road name (string)
        
    Returns:
        str or None: The road type if found, otherwise None
    """
    # Search from right to left for road types
    for road_type in ROAD_TYPES:
        # Look for the road type at the end of the name, preceded by a space
        search_pattern = ' ' + road_type
        if road_name.endswith(search_pattern):
            return road_type
        # Also check case-insensitive match
        if road_name.lower().endswith(search_pattern.lower()):
            return road_type
        # Also check if the entire name is just the road type (edge case)
        if road_name.lower() == road_type.lower():
            return road_type
    
    return None


def extract_road_data(G):
    """
    Extract road segment data from the OSMnx graph.
    
    Args:
        G: networkx.MultiDiGraph from OSMnx
        
    Returns:
        list: List of dictionaries containing road segment information
    """
    roads_data = []
    
    for u, v, key, data in G.edges(keys=True, data=True):
        # Get node coordinates
        u_node = G.nodes[u]
        v_node = G.nodes[v]
        
        # Extract geometry if available, otherwise use straight line
        if 'geometry' in data:
            coords = list(data['geometry'].coords)
        else:
            coords = [(u_node['x'], u_node['y']), (v_node['x'], v_node['y'])]
        
        # Get road name and normalize if it's a list
        road_name = normalize_road_name(data.get('name', 'Unknown'))
        
        # Skip roads named "unnamed" (case-insensitive)
        if road_name.lower() == 'unnamed':
            continue
        
        # Build road segment dictionary
        road_segment = {
            'edge_id': f"{u}_{v}_{key}",
            'start_node': u,
            'end_node': v,
            'coordinates': coords,
            'name': road_name,
            'highway': data.get('highway', 'unknown'),
            'length': data.get('length', 0),
            'oneway': data.get('oneway', False),
            'osmid': data.get('osmid', None)
        }
        
        roads_data.append(road_segment)
    
    return roads_data


def calculate_distance(point1, point2):
    """
    Calculate Euclidean distance between two coordinate points.
    
    Args:
        point1: Tuple of (x, y) coordinates
        point2: Tuple of (x, y) coordinates
        
    Returns:
        float: Distance between the points
    """
    return math.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)


def find_closest_segment(start_point, remaining_segments, used_indices):
    """
    Find the closest unused segment to the given start point.
    
    Args:
        start_point: Tuple of (x, y) coordinates
        remaining_segments: List of remaining road segments
        used_indices: Set of already used segment indices
        
    Returns:
        tuple: (index, segment, reversed) where reversed indicates if segment should be flipped
    """
    min_distance = float('inf')
    best_idx = None
    best_reversed = False
    
    for idx, segment in enumerate(remaining_segments):
        if idx in used_indices:
            continue
        
        coords = segment['coordinates']
        first_point = coords[0]
        last_point = coords[-1]
        
        # Check distance to both ends of the segment
        dist_to_first = calculate_distance(start_point, first_point)
        dist_to_last = calculate_distance(start_point, last_point)
        
        if dist_to_first < min_distance:
            min_distance = dist_to_first
            best_idx = idx
            best_reversed = False
        
        if dist_to_last < min_distance:
            min_distance = dist_to_last
            best_idx = idx
            best_reversed = True
    
    return best_idx, best_reversed, min_distance


def combine_segments(segments):
    """
    Combine road segments into a continuous path using a greedy sorting algorithm.
    
    Args:
        segments: List of road segments for the same road
        
    Returns:
        tuple: (segment_coords_list, total_length) where segment_coords_list is a list
               of coordinate arrays (one per segment) and total_length is the
               sum of all segment lengths
    """
    if not segments:
        return [], 0.0
    
    if len(segments) == 1:
        segment_length = segments[0].get('length', 0.0)
        return [segments[0]['coordinates']], segment_length
    
    # Initialize with first segment
    segment_list = [list(segments[0]['coordinates'])]
    total_length = segments[0].get('length', 0.0)
    used_indices = {0}
    
    # Keep adding segments until all are used
    while len(used_indices) < len(segments):
        # Get the last point of our combined path
        last_point = segment_list[-1][-1]
        
        # Find the closest unused segment
        idx, reversed_flag, distance = find_closest_segment(last_point, segments, used_indices)
        
        if idx is None:
            # No more connectable segments, try from beginning
            first_point = segment_list[0][0]
            idx, reversed_flag, distance = find_closest_segment(first_point, segments, used_indices)
            
            if idx is None:
                break
            
            new_coords = segments[idx]['coordinates']
            if reversed_flag:
                new_coords = list(reversed(new_coords))
            
            segment_list.insert(0, new_coords)
        else:
            new_coords = segments[idx]['coordinates']
            if reversed_flag:
                new_coords = list(reversed(new_coords))
            
            segment_list.append(new_coords)
        
        # Add the length of this segment
        total_length += segments[idx].get('length', 0.0)
        used_indices.add(idx)
    
    return segment_list, total_length


def calculate_size_categories(formatted_roads):
    """
    Calculate size categories (big, medium, small) for roads based on length percentiles.
    
    Roads are categorized as:
    - big: top 33% of roads by length
    - medium: middle 33% of roads by length
    - small: bottom 33% of roads by length
    
    Args:
        formatted_roads: Dictionary of formatted road data with length field
        
    Returns:
        dict: Dictionary mapping road names to size categories
    """
    if not formatted_roads:
        return {}
    
    # Extract lengths and sort them
    road_lengths = [(name, data['length']) for name, data in formatted_roads.items()]
    road_lengths.sort(key=lambda x: x[1])
    
    total_roads = len(road_lengths)
    
    # Calculate the indices for 33rd and 66th percentiles
    small_count = total_roads // 3
    medium_count = total_roads // 3
    
    size_map = {}
    
    for i, (name, length) in enumerate(road_lengths):
        if i < small_count:
            size_map[name] = 'small'
        elif i < small_count + medium_count:
            size_map[name] = 'medium'
        else:
            size_map[name] = 'big'
    
    return size_map


def group_and_combine_roads(roads_data, district_id=None):
    """
    Group road segments by name and combine them.
    
    Args:
        roads_data: List of raw road segments
        district_id: Optional district ID to include in road objects
        
    Returns:
        dict: Dictionary mapping road names to combined road objects
    """
    # Group segments by road name
    roads_by_name = defaultdict(list)
    
    for segment in roads_data:
        road_name = segment.get('name', 'Unknown')
        
        # Normalize road name (handle list names from OSM data)
        road_name = normalize_road_name(road_name)
        
        # Skip unnamed roads or consolidate them
        if road_name and road_name != 'Unknown' and road_name.lower() != 'unnamed':
            roads_by_name[road_name].append(segment)
    
    # Combine segments for each road
    formatted_roads = {}
    
    for road_name, segments in roads_by_name.items():
        print(f"Processing {road_name}: {len(segments)} segments")
        combined_coords, total_length = combine_segments(segments)
        
        # Extract road type
        road_type = extract_road_type(road_name)
        
        # Build road object with new format
        road_obj = {
            'name': road_name,
            'road_type': road_type,
            'coordinates': combined_coords,
            'length': total_length,
            'segments': len(segments),
            'areas': [],
            'sub_areas': []
        }
        
        # Add district_id if provided
        if district_id is not None:
            road_obj['district_id'] = district_id
        
        formatted_roads[road_name] = road_obj
    
    # Calculate and add size categories
    size_map = calculate_size_categories(formatted_roads)
    for road_name in formatted_roads:
        formatted_roads[road_name]['size'] = size_map[road_name]
    
    return formatted_roads


def load_raw_roads(input_file):
    """
    Load raw road segments from JSON file (for offline mode).
    
    Args:
        input_file: Path to the raw roads JSON file
        
    Returns:
        list: List of road segment dictionaries
    """
    with open(input_file, 'r') as f:
        roads_data = json.load(f)
    return roads_data


def save_roads_data(roads_data, output_file):
    """
    Save the roads data to a JSON file.
    
    Args:
        roads_data: Dictionary of road data
        output_file: Path to output JSON file
    """
    with open(output_file, 'w') as f:
        json.dump(roads_data, f, indent=2)
    
    print(f"Saved {len(roads_data)} roads to {output_file}")


def main():
    """Main execution function."""
    import sys
    import os
    
    # Check if we should use offline mode (if roads_raw.json exists and no --online flag)
    use_offline = os.path.exists('roads_raw.json') and '--online' not in sys.argv
    
    input_geojson = 'my_district.geojson'
    output_json = 'roads_formatted.json'
    
    # Parse command line arguments for district_id
    district_id = None
    for arg in sys.argv[1:]:
        if arg.startswith('--district-id='):
            district_id = arg.split('=', 1)[1]
            # Try to convert to int if it's a number
            try:
                district_id = int(district_id)
            except ValueError:
                pass  # Keep as string
    
    if use_offline:
        print("Using offline mode with existing roads_raw.json")
        print("(Use --online flag to fetch fresh data from OpenStreetMap)")
        print()
        print("Loading raw roads from roads_raw.json...")
        roads_data = load_raw_roads('roads_raw.json')
    else:
        print(f"Loading district polygon from {input_geojson}...")
        polygon = load_district_polygon(input_geojson)
        
        print("Fetching roads from OpenStreetMap...")
        G = get_roads_from_polygon(polygon)
        
        print(f"Extracting data from {len(G.edges)} road segments...")
        roads_data = extract_road_data(G)
    
    print(f"Processing {len(roads_data)} road segments...")
    if district_id is not None:
        print(f"Using district_id: {district_id}")
    formatted_roads = group_and_combine_roads(roads_data, district_id=district_id)
    
    print(f"Saving formatted roads to {output_json}...")
    save_roads_data(formatted_roads, output_json)
    
    print("Done!")


if __name__ == '__main__':
    main()
