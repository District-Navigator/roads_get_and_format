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
        list: Combined list of coordinate points forming the complete road
    """
    if not segments:
        return []
    
    if len(segments) == 1:
        return segments[0]['coordinates']
    
    # Start with the first segment
    combined_coords = list(segments[0]['coordinates'])
    used_indices = {0}
    
    # Keep adding segments until all are used
    while len(used_indices) < len(segments):
        # Get the last point of our combined path
        last_point = combined_coords[-1]
        
        # Find the closest unused segment
        idx, reversed_flag, distance = find_closest_segment(last_point, segments, used_indices)
        
        if idx is None:
            # No more connectable segments, try from beginning
            first_point = combined_coords[0]
            idx, reversed_flag, distance = find_closest_segment(first_point, segments, used_indices)
            
            if idx is None:
                break
            
            # Add to beginning of path
            new_coords = segments[idx]['coordinates']
            if reversed_flag:
                new_coords = list(reversed(new_coords))
            
            # Avoid duplicate point at connection
            if new_coords[-1] != combined_coords[0]:
                combined_coords = new_coords + combined_coords
            else:
                combined_coords = new_coords[:-1] + combined_coords
        else:
            # Add to end of path
            new_coords = segments[idx]['coordinates']
            if reversed_flag:
                new_coords = list(reversed(new_coords))
            
            # Avoid duplicate point at connection
            if new_coords[0] != combined_coords[-1]:
                combined_coords.extend(new_coords)
            else:
                combined_coords.extend(new_coords[1:])
        
        used_indices.add(idx)
    
    return combined_coords


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
        
        # Handle list names (some OSM roads have multiple names)
        if isinstance(road_name, list):
            # Join multiple names with " / " separator
            road_name = ' / '.join(str(name) for name in road_name if name)
            if not road_name:
                road_name = 'Unknown'
        
        # Skip unnamed roads or consolidate them
        if road_name and road_name != 'Unknown':
            roads_by_name[road_name].append(segment)
    
    # Combine segments for each road
    formatted_roads = {}
    
    for road_name, segments in roads_by_name.items():
        print(f"Processing {road_name}: {len(segments)} segments")
        combined_coords = combine_segments(segments)
        
        formatted_roads[road_name] = {
            'name': road_name,
            'coordinates': combined_coords,
            'segment_count': len(segments),
            'total_points': len(combined_coords)
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
