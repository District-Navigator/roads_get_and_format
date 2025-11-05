#!/usr/bin/env python3
"""
Format Roads from OpenStreetMap Data
Reads roads.json from step 2 and formats it into a structured format.
Groups road segments by name and determines which areas/sub_areas each road is in.
"""

import argparse
import json
import math
import os
import sys


def load_json_file(filepath):
    """
    Load a JSON file.
    
    Args:
        filepath: Path to the JSON file
        
    Returns:
        dict: Parsed JSON data, or None if error
    """
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading {filepath}: {e}", file=sys.stderr)
        return None


def load_area_files(areas_dir):
    """
    Load all GeoJSON area files from a directory.
    
    Args:
        areas_dir: Path to directory containing area GeoJSON files
        
    Returns:
        dict: Dictionary mapping area names to their geometry
    """
    areas = {}
    
    if not os.path.exists(areas_dir):
        return areas
    
    for filename in os.listdir(areas_dir):
        if filename.endswith('.geojson') and filename != '.gitkeep':
            filepath = os.path.join(areas_dir, filename)
            data = load_json_file(filepath)
            
            if data and 'features' in data and len(data['features']) > 0:
                # Extract area name from filename (remove .geojson extension)
                area_name = filename[:-8]
                geometry = data['features'][0].get('geometry')
                
                if geometry:
                    areas[area_name] = geometry
    
    return areas


def point_in_polygon(point, polygon_coords):
    """
    Check if a point is inside a polygon using ray casting algorithm.
    
    Args:
        point: [lon, lat] coordinates
        polygon_coords: List of [lon, lat] coordinates forming the polygon
        
    Returns:
        bool: True if point is inside polygon
    """
    lon, lat = point
    inside = False
    
    n = len(polygon_coords)
    p1_lon, p1_lat = polygon_coords[0]
    
    for i in range(n + 1):
        p2_lon, p2_lat = polygon_coords[i % n]
        
        if lat > min(p1_lat, p2_lat):
            if lat <= max(p1_lat, p2_lat):
                if lon <= max(p1_lon, p2_lon):
                    if p1_lat != p2_lat:
                        x_intersect = (lat - p1_lat) * (p2_lon - p1_lon) / (p2_lat - p1_lat) + p1_lon
                        if p1_lon == p2_lon or lon <= x_intersect:
                            inside = not inside
        
        p1_lon, p1_lat = p2_lon, p2_lat
    
    return inside


def get_areas_for_coordinates(coordinates, areas):
    """
    Determine which areas contain any of the given coordinates.
    
    Args:
        coordinates: List of coordinate arrays (one per segment)
        areas: Dictionary mapping area names to their geometry
        
    Returns:
        list: Names of areas that contain at least one coordinate
    """
    found_areas = set()
    
    for area_name, geometry in areas.items():
        geom_type = geometry.get('type')
        
        # Handle Polygon geometry
        if geom_type == 'Polygon':
            polygon_coords = geometry['coordinates'][0]
            
            # Check each segment's coordinates
            for segment in coordinates:
                for coord in segment:
                    if point_in_polygon(coord, polygon_coords):
                        found_areas.add(area_name)
                        break
                if area_name in found_areas:
                    break
        
        # Handle MultiPolygon geometry
        elif geom_type == 'MultiPolygon':
            # Check each polygon in the MultiPolygon
            for polygon in geometry['coordinates']:
                polygon_coords = polygon[0]
                
                for segment in coordinates:
                    for coord in segment:
                        if point_in_polygon(coord, polygon_coords):
                            found_areas.add(area_name)
                            break
                    if area_name in found_areas:
                        break
                
                if area_name in found_areas:
                    break
    
    return sorted(list(found_areas))


def haversine_distance(coord1, coord2):
    """
    Calculate the great circle distance between two points on Earth.
    
    Args:
        coord1: [lon, lat] first coordinate
        coord2: [lon, lat] second coordinate
        
    Returns:
        float: Distance in meters
    """
    # Earth's radius in meters
    R = 6371000
    
    lon1, lat1 = coord1
    lon2, lat2 = coord2
    
    # Convert to radians
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    # Haversine formula
    a = math.sin(delta_lat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    
    return R * c


def calculate_segment_length(coordinates):
    """
    Calculate the total length of a coordinate segment.
    
    Args:
        coordinates: List of [lon, lat] coordinates
        
    Returns:
        float: Total length in meters
    """
    if len(coordinates) < 2:
        return 0.0
    
    total_length = 0
    
    for i in range(len(coordinates) - 1):
        total_length += haversine_distance(coordinates[i], coordinates[i + 1])
    
    return total_length


def calculate_total_length(coordinate_segments):
    """
    Calculate the total length of all coordinate segments.
    
    Args:
        coordinate_segments: List of coordinate arrays
        
    Returns:
        float: Total length in meters
    """
    total_length = 0
    
    for segment in coordinate_segments:
        total_length += calculate_segment_length(segment)
    
    return total_length


def extract_road_type(road_name):
    """
    Extract the road type from the road name.
    E.g., "Fairwood Drive" -> "Drive"
    
    Args:
        road_name: Full road name
        
    Returns:
        str: Road type or empty string if not found
    """
    common_types = [
        'Street', 'Road', 'Avenue', 'Drive', 'Lane', 'Way', 'Court', 'Place',
        'Circle', 'Boulevard', 'Parkway', 'Highway', 'Trail', 'Path', 'Terrace',
        'Plaza', 'Row', 'Alley', 'Walk', 'Run', 'Ridge', 'Crossing', 'Bend',
        # Common abbreviations
        'St', 'Rd', 'Ave', 'Dr', 'Ln', 'Blvd', 'Pkwy', 'Hwy', 'Cir', 'Ct', 'Pl'
    ]
    
    words = road_name.split()
    
    # Check last word for exact match (case-insensitive)
    if words:
        last_word = words[-1]
        for road_type in common_types:
            if last_word.lower() == road_type.lower():
                # Return the original case from the road name
                return last_word
    
    return ""


def determine_size(length):
    """
    Determine road size category based on length.
    
    Args:
        length: Road length in meters
        
    Returns:
        str: Size category (small, medium, large)
    """
    if length < 500:
        return "small"
    elif length < 1000:
        return "medium"
    else:
        return "large"


def format_roads(roads_data, areas, sub_areas):
    """
    Format roads data into the specified structure.
    
    Args:
        roads_data: Raw roads data from Overpass API
        areas: Dictionary of area geometries
        sub_areas: Dictionary of sub-area geometries
        
    Returns:
        dict: Formatted roads data
    """
    # Build a lookup for nodes
    nodes = {}
    ways = []
    
    for element in roads_data.get('elements', []):
        if element.get('type') == 'node':
            nodes[element['id']] = [element['lon'], element['lat']]
        elif element.get('type') == 'way':
            ways.append(element)
    
    # Group ways by road name
    roads_by_name = {}
    
    for way in ways:
        tags = way.get('tags', {})
        name = tags.get('name', 'Unnamed Road')
        
        # Skip ways without coordinates
        node_ids = way.get('nodes', [])
        if not node_ids:
            continue
        
        # Convert node IDs to coordinates
        coordinates = []
        for node_id in node_ids:
            if node_id in nodes:
                coordinates.append(nodes[node_id])
        
        if not coordinates:
            continue
        
        # Initialize road entry if it doesn't exist
        if name not in roads_by_name:
            roads_by_name[name] = {
                'name': name,
                'road_type': extract_road_type(name),
                'coordinates': [],
                'segments': 0
            }
        
        # Add this segment's coordinates
        roads_by_name[name]['coordinates'].append(coordinates)
        roads_by_name[name]['segments'] += 1
    
    # Calculate length, areas, and size for each road
    formatted_roads = {}
    
    for name, road_data in roads_by_name.items():
        # Calculate total length
        length = calculate_total_length(road_data['coordinates'])
        road_data['length'] = length
        
        # Determine which areas the road is in
        road_areas = get_areas_for_coordinates(road_data['coordinates'], areas)
        road_data['areas'] = road_areas
        
        # Determine which sub-areas the road is in
        road_sub_areas = get_areas_for_coordinates(road_data['coordinates'], sub_areas)
        road_data['sub_areas'] = road_sub_areas
        
        # Determine size
        road_data['size'] = determine_size(length)
        
        formatted_roads[name] = road_data
    
    return formatted_roads


def save_formatted_roads(formatted_roads, output_path):
    """
    Save formatted roads to a JSON file.
    
    Args:
        formatted_roads: Formatted roads dictionary
        output_path: Path to save the JSON file
    """
    try:
        with open(output_path, 'w') as f:
            json.dump(formatted_roads, f, indent=2)
        print(f"Formatted roads saved to: {output_path}", file=sys.stderr)
    except Exception as e:
        print(f"Error saving formatted roads: {e}", file=sys.stderr)
        raise


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description='Format roads from OpenStreetMap data into structured format'
    )
    parser.add_argument(
        '--input',
        type=str,
        default='roads.json',
        help='Path to input roads JSON file from step 2 (default: roads.json)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='formatted_roads.json',
        help='Path to output formatted JSON file (default: formatted_roads.json)'
    )
    parser.add_argument(
        '--areas-dir',
        type=str,
        default='areas',
        help='Path to directory containing area GeoJSON files (default: areas)'
    )
    parser.add_argument(
        '--sub-areas-dir',
        type=str,
        default='sub_areas',
        help='Path to directory containing sub-area GeoJSON files (default: sub_areas)'
    )
    
    args = parser.parse_args()
    
    # Resolve paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    input_path = args.input
    if not os.path.isabs(input_path):
        input_path = os.path.join(script_dir, input_path)
    
    output_path = args.output
    if not os.path.isabs(output_path):
        output_path = os.path.join(script_dir, output_path)
    
    areas_dir = args.areas_dir
    if not os.path.isabs(areas_dir):
        areas_dir = os.path.join(script_dir, areas_dir)
    
    sub_areas_dir = args.sub_areas_dir
    if not os.path.isabs(sub_areas_dir):
        sub_areas_dir = os.path.join(script_dir, sub_areas_dir)
    
    print(f"Loading roads from: {input_path}", file=sys.stderr)
    
    # Load roads data
    roads_data = load_json_file(input_path)
    if not roads_data:
        print("Error: Could not load roads data", file=sys.stderr)
        return 1
    
    print(f"Loading areas from: {areas_dir}", file=sys.stderr)
    areas = load_area_files(areas_dir)
    print(f"Loaded {len(areas)} areas: {', '.join(areas.keys())}", file=sys.stderr)
    
    print(f"Loading sub-areas from: {sub_areas_dir}", file=sys.stderr)
    sub_areas = load_area_files(sub_areas_dir)
    print(f"Loaded {len(sub_areas)} sub-areas: {', '.join(sub_areas.keys())}", file=sys.stderr)
    
    try:
        # Format the roads
        print("Formatting roads...", file=sys.stderr)
        formatted_roads = format_roads(roads_data, areas, sub_areas)
        
        print(f"\nFormatted {len(formatted_roads)} roads:", file=sys.stderr)
        for name, road in list(formatted_roads.items())[:5]:  # Show first 5
            print(f"  - {name}: {road['segments']} segments, {road['length']:.2f}m, areas: {road['areas']}", file=sys.stderr)
        
        if len(formatted_roads) > 5:
            print(f"  ... and {len(formatted_roads) - 5} more", file=sys.stderr)
        
        # Save the formatted data
        save_formatted_roads(formatted_roads, output_path)
        
        print(f"\nSuccess! Formatted roads saved.", file=sys.stderr)
        return 0
        
    except Exception as e:
        print(f"\nFailed to format roads: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
