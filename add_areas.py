#!/usr/bin/env python3
"""
Program 2: Add Areas and Sub-Areas to Formatted Roads
Takes roads_formatted.json and adds 'areas' and 'sub_areas' fields to each road.
For each area in the areas/ folder and sub-area in the sub_areas/ folder,
checks if any road coordinates fall within that polygon.
Updates roads_formatted.json in place.
"""

import json
import os
from pathlib import Path
from shapely.geometry import Point, Polygon


def load_area_geojson(area_file):
    """
    Load an area polygon from a GeoJSON file.
    
    Args:
        area_file: Path to the area GeoJSON file
        
    Returns:
        tuple: (area_name, Polygon) - The area name and its polygon geometry
    """
    with open(area_file, 'r') as f:
        geojson_data = json.load(f)
    
    # Extract area name from filename (e.g., "station-8.geojson" -> "station-8")
    area_name = Path(area_file).stem
    
    # Extract polygon coordinates from GeoJSON
    # Assuming FeatureCollection with one Feature containing a Polygon
    if geojson_data['type'] == 'FeatureCollection':
        features = geojson_data['features']
        if features:
            geometry = features[0]['geometry']
            if geometry['type'] == 'Polygon':
                # GeoJSON coordinates are [longitude, latitude]
                coords = geometry['coordinates'][0]  # First ring (outer boundary)
                polygon = Polygon(coords)
                return area_name, polygon
    
    return None, None


def load_all_areas(areas_folder):
    """
    Load all area polygons from the areas folder.
    
    Args:
        areas_folder: Path to the folder containing area GeoJSON files
        
    Returns:
        dict: Dictionary mapping area names to Shapely Polygon objects
    """
    areas = {}
    areas_path = Path(areas_folder)
    
    if not areas_path.exists():
        print(f"Warning: Areas folder '{areas_folder}' not found")
        return areas
    
    # Find all .geojson files
    geojson_files = list(areas_path.glob('*.geojson'))
    
    if not geojson_files:
        print(f"Warning: No .geojson files found in '{areas_folder}'")
        return areas
    
    print(f"Loading {len(geojson_files)} area(s) from {areas_folder}...")
    
    for area_file in geojson_files:
        area_name, polygon = load_area_geojson(area_file)
        if area_name and polygon:
            areas[area_name] = polygon
            print(f"  Loaded area: {area_name}")
        else:
            print(f"  Warning: Could not load area from {area_file}")
    
    return areas


def check_road_in_area(road_data, polygon):
    """
    Check if any coordinate of a road falls within an area polygon.
    
    Args:
        road_data: Dictionary containing road data with 'coordinates' field
        polygon: Shapely Polygon object representing the area
        
    Returns:
        bool: True if any coordinate is within the polygon, False otherwise
    """
    # road_data['coordinates'] is a list of segments
    # Each segment is a list of [longitude, latitude] points
    for segment in road_data['coordinates']:
        for coord in segment:
            # coord is [longitude, latitude]
            point = Point(coord[0], coord[1])
            if polygon.contains(point):
                return True
    
    return False


def add_areas_to_roads(formatted_roads, areas, sub_areas):
    """
    Add area and sub-area information to each road based on coordinate intersection.
    
    Args:
        formatted_roads: Dictionary of formatted road data
        areas: Dictionary mapping area names to Shapely Polygon objects
        sub_areas: Dictionary mapping sub-area names to Shapely Polygon objects
        
    Returns:
        dict: Updated formatted_roads with 'areas' and 'sub_areas' fields
    """
    print(f"\nProcessing {len(formatted_roads)} roads against {len(areas)} areas and {len(sub_areas)} sub-areas...")
    
    # Initialize areas and sub_areas fields for all roads if they don't exist
    for road_name in formatted_roads:
        if 'areas' not in formatted_roads[road_name]:
            formatted_roads[road_name]['areas'] = []
        if 'sub_areas' not in formatted_roads[road_name]:
            formatted_roads[road_name]['sub_areas'] = []
    
    # Process areas
    if areas:
        for area_name, polygon in areas.items():
            print(f"\nChecking area '{area_name}'...")
            roads_in_area = 0
            
            for road_name, road_data in formatted_roads.items():
                if check_road_in_area(road_data, polygon):
                    if area_name not in formatted_roads[road_name]['areas']:
                        formatted_roads[road_name]['areas'].append(area_name)
                    roads_in_area += 1
            
            print(f"  Found {roads_in_area} roads in '{area_name}'")
    
    # Process sub-areas
    if sub_areas:
        for sub_area_name, polygon in sub_areas.items():
            print(f"\nChecking sub-area '{sub_area_name}'...")
            roads_in_sub_area = 0
            
            for road_name, road_data in formatted_roads.items():
                if check_road_in_area(road_data, polygon):
                    if sub_area_name not in formatted_roads[road_name]['sub_areas']:
                        formatted_roads[road_name]['sub_areas'].append(sub_area_name)
                    roads_in_sub_area += 1
            
            print(f"  Found {roads_in_sub_area} roads in '{sub_area_name}'")
    
    # Report summary statistics
    roads_with_areas = sum(1 for road in formatted_roads.values() if road['areas'])
    roads_with_sub_areas = sum(1 for road in formatted_roads.values() if road['sub_areas'])
    roads_without_any = sum(1 for road in formatted_roads.values() 
                            if not road['areas'] and not road['sub_areas'])
    
    print(f"\nSummary:")
    print(f"  Roads with at least one area: {roads_with_areas}")
    print(f"  Roads with at least one sub-area: {roads_with_sub_areas}")
    print(f"  Roads with no areas or sub-areas: {roads_without_any}")
    
    # Show distribution of roads by number of areas
    if areas:
        area_counts = {}
        for road in formatted_roads.values():
            count = len(road['areas'])
            area_counts[count] = area_counts.get(count, 0) + 1
        
        print(f"\nDistribution by number of areas:")
        for count in sorted(area_counts.keys()):
            print(f"  {count} area(s): {area_counts[count]} roads")
    
    # Show distribution of roads by number of sub-areas
    if sub_areas:
        sub_area_counts = {}
        for road in formatted_roads.values():
            count = len(road['sub_areas'])
            sub_area_counts[count] = sub_area_counts.get(count, 0) + 1
        
        print(f"\nDistribution by number of sub-areas:")
        for count in sorted(sub_area_counts.keys()):
            print(f"  {count} sub-area(s): {sub_area_counts[count]} roads")
    
    return formatted_roads


def load_formatted_roads(input_file):
    """
    Load formatted roads from JSON file.
    
    Args:
        input_file: Path to the formatted roads JSON file
        
    Returns:
        dict: Dictionary of formatted road data
    """
    with open(input_file, 'r') as f:
        return json.load(f)


def save_formatted_roads(formatted_roads, output_file):
    """
    Save the formatted roads data to a JSON file.
    
    Args:
        formatted_roads: Dictionary of formatted road data
        output_file: Path to output JSON file
    """
    with open(output_file, 'w') as f:
        json.dump(formatted_roads, f, indent=2)
    
    print(f"\nSaved updated roads to {output_file}")


def main():
    """Main execution function."""
    input_json = 'roads_formatted.json'
    areas_folder = 'areas'
    sub_areas_folder = 'sub_areas'
    
    # Load formatted roads
    print(f"Loading formatted roads from {input_json}...")
    formatted_roads = load_formatted_roads(input_json)
    print(f"Loaded {len(formatted_roads)} roads")
    
    # Load all areas
    areas = load_all_areas(areas_folder)
    
    # Load all sub-areas
    sub_areas = load_all_areas(sub_areas_folder)
    
    if not areas and not sub_areas:
        print("No areas or sub-areas found. Exiting without making changes.")
        return
    
    # Add area and sub-area information to roads
    updated_roads = add_areas_to_roads(formatted_roads, areas, sub_areas)
    
    # Save back to the same file (updating in place)
    save_formatted_roads(updated_roads, input_json)
    
    print("\nDone!")


if __name__ == '__main__':
    main()
