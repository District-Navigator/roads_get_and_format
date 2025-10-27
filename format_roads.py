#!/usr/bin/env python3
"""
Program 2: Format and Combine Road Segments
Takes the raw road data from roads_raw.json, groups segments by road name,
and combines them using a sorting algorithm to create continuous road paths.
Outputs formatted roads to roads_formatted.json
"""

import json
import math
from collections import defaultdict

# List of valid road types for extraction
ROAD_TYPES = [
    'Avenue', 'Bay', 'Boulevard', 'Circle', 'Court', 'Cove', 'Drive',
    'Expressway', 'Lane', 'Parkway', 'Place', 'Road', 'Row', 'Spur',
    'Street', 'Way'
]


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
    # We need to ensure the road type starts with a space (or is at the beginning)
    # to avoid matching "way" in "Parkway"
    for road_type in ROAD_TYPES:
        # Look for the road type at the end of the name, preceded by a space
        # Use case-insensitive matching to handle variations like "Main street" or "Oak AVENUE"
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


def load_raw_roads(input_file):
    """
    Load raw road segments from JSON file.
    
    Args:
        input_file: Path to the raw roads JSON file
        
    Returns:
        list: List of road segment dictionaries
    """
    with open(input_file, 'r') as f:
        roads_data = json.load(f)
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


def group_and_combine_roads(roads_data):
    """
    Group road segments by name and combine them.
    
    Args:
        roads_data: List of raw road segments
        
    Returns:
        dict: Dictionary mapping road names to combined coordinate lists
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
        
        # Calculate total points across all segments
        total_points = sum(len(seg) for seg in combined_coords)
        
        formatted_roads[road_name] = {
            'name': road_name,
            'road_type': road_type,
            'coordinates': combined_coords,
            'segment_count': len(segments),
            'total_points': total_points,
            'length': total_length
        }
    
    return formatted_roads


def save_formatted_roads(formatted_roads, output_file):
    """
    Save the formatted roads data to a JSON file.
    
    Args:
        formatted_roads: Dictionary of formatted road data
        output_file: Path to output JSON file
    """
    with open(output_file, 'w') as f:
        json.dump(formatted_roads, f, indent=2)
    
    print(f"Saved {len(formatted_roads)} roads to {output_file}")


def main():
    """Main execution function."""
    input_json = 'roads_raw.json'
    output_json = 'roads_formatted.json'
    
    print(f"Loading raw roads from {input_json}...")
    roads_data = load_raw_roads(input_json)
    
    print(f"Processing {len(roads_data)} road segments...")
    formatted_roads = group_and_combine_roads(roads_data)
    
    print(f"Saving formatted roads to {output_json}...")
    save_formatted_roads(formatted_roads, output_json)
    
    print("Done!")


if __name__ == '__main__':
    main()
