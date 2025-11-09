#!/usr/bin/env python3
"""
Create Roads SQL Query Generator
Generates SQL INSERT queries for adding roads to the database.
Reads from formatted_roads.json and creates SQL statements with coordinates.
Supports interactive area name to ID mapping.
"""

import argparse
import json
import os
import sys
import re

# ============================================================================
# INPUT VARIABLES - Edit these values when running in PyCharm/IDE
# ============================================================================
DISTRICT_ID = 1
FORMATTED_ROADS_FILE = "formatted_roads.json"
OUTPUT_FILE = "step_6_output.txt"
AREA_MAPPINGS_FILE = None  # Optional: Path to area mappings JSON file
# ============================================================================


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


def collect_unique_areas_and_sub_areas(formatted_roads):
    """
    Collect all unique area and sub-area names from formatted roads.
    
    Args:
        formatted_roads: Dictionary of formatted road data
        
    Returns:
        tuple: (set of area names, set of sub-area names)
    """
    area_names = set()
    sub_area_names = set()
    
    for name, road_data in formatted_roads.items():
        # Collect areas
        areas = road_data.get('areas', [])
        if isinstance(areas, list):
            area_names.update(areas)
        
        # Collect sub_areas
        sub_areas = road_data.get('sub_areas', [])
        if isinstance(sub_areas, list):
            sub_area_names.update(sub_areas)
    
    return area_names, sub_area_names


def prompt_for_area_mapping(area_name, mapping_type="area"):
    """
    Prompt user for area ID mapping.
    
    Args:
        area_name: Name of the area
        mapping_type: Type of mapping ("area" or "sub-area")
        
    Returns:
        int or None: Area ID, or None if skipped
    """
    while True:
        response = input(f"Enter ID for {mapping_type} '{area_name}' (or press Enter to skip): ").strip()
        
        if not response:
            return None
        
        try:
            area_id = int(response)
            if area_id <= 0:
                print(f"Invalid input. Please enter a positive integer ID or press Enter to skip.", file=sys.stderr)
                continue
            return area_id
        except ValueError:
            print(f"Invalid input. Please enter a positive integer ID or press Enter to skip.", file=sys.stderr)


def load_or_create_area_mappings(formatted_roads, mappings_file=None, interactive=True):
    """
    Load area mappings from file or prompt user interactively.
    
    Args:
        formatted_roads: Dictionary of formatted road data
        mappings_file: Optional path to JSON file with area mappings
        interactive: Whether to prompt for missing mappings
        
    Returns:
        tuple: (area_id_map dict, sub_area_id_map dict)
    """
    area_id_map = {}
    sub_area_id_map = {}
    
    # Try to load from file first
    if mappings_file and os.path.exists(mappings_file):
        print(f"Loading area mappings from {mappings_file}...")
        mappings = load_json_file(mappings_file)
        if mappings:
            area_id_map = mappings.get('areas', {})
            sub_area_id_map = mappings.get('sub_areas', {})
            print(f"Loaded {len(area_id_map)} area mappings and {len(sub_area_id_map)} sub-area mappings")
    
    if not interactive:
        return area_id_map, sub_area_id_map
    
    # Collect unique areas and sub-areas
    area_names, sub_area_names = collect_unique_areas_and_sub_areas(formatted_roads)
    
    # Prompt for missing area mappings
    if area_names:
        print(f"\nFound {len(area_names)} unique areas in the data.")
        missing_areas = [name for name in sorted(area_names) if name not in area_id_map]
        
        if missing_areas:
            print("Please provide IDs for the following areas:")
            for area_name in missing_areas:
                area_id = prompt_for_area_mapping(area_name, "area")
                if area_id is not None:
                    area_id_map[area_name] = area_id
    
    # Prompt for missing sub-area mappings
    if sub_area_names:
        print(f"\nFound {len(sub_area_names)} unique sub-areas in the data.")
        missing_sub_areas = [name for name in sorted(sub_area_names) if name not in sub_area_id_map]
        
        if missing_sub_areas:
            print("Please provide IDs for the following sub-areas:")
            for sub_area_name in missing_sub_areas:
                sub_area_id = prompt_for_area_mapping(sub_area_name, "sub-area")
                if sub_area_id is not None:
                    sub_area_id_map[sub_area_name] = sub_area_id
    
    return area_id_map, sub_area_id_map


def generate_road_key(name):
    """
    Generate a stable key/slug from a road name.
    Converts to lowercase, replaces spaces and special chars with hyphens.
    
    Args:
        name: Road name
        
    Returns:
        str: URL-safe key
    """
    # Convert to lowercase
    key = name.lower()
    # Replace spaces and special characters with hyphens
    key = re.sub(r'[^a-z0-9]+', '-', key)
    # Remove leading/trailing hyphens
    key = key.strip('-')
    return key


def generate_unmapped_warning(names, id_map, type_label):
    """
    Generate warning comment for unmapped area/sub-area names.
    
    Args:
        names: List of area/sub-area names
        id_map: Optional mapping dict from names to IDs
        type_label: Label for the type ("areas" or "sub-areas")
        
    Returns:
        str: Warning comment or empty string
    """
    if not names:
        return ""
    
    if not id_map:
        return f"-- Road references {type_label} by name: {', '.join(names)}\n"
    
    unmapped = [name for name in names if name not in id_map]
    if unmapped:
        return f"-- Warning: Unmapped {type_label} names: {', '.join(unmapped)}\n"
    
    return ""


def generate_road_insert_query(district_id, name, road_data, area_id_map=None, sub_area_id_map=None):
    """
    Generate an SQL INSERT query for adding a road to the database.
    
    Args:
        district_id: District ID (INTEGER, FK to districts.id)
        name: Road name (TEXT, required)
        road_data: Road data from formatted_roads.json
        area_id_map: Optional dict mapping area names to IDs
        sub_area_id_map: Optional dict mapping sub-area names to IDs
        
    Returns:
        str: SQL INSERT query
    """
    # Validate inputs
    if not isinstance(district_id, int):
        try:
            district_id = int(district_id)
        except (ValueError, TypeError):
            raise ValueError("district_id must be an integer")
    
    if not name or not name.strip():
        raise ValueError("Road name cannot be empty")
    
    # Generate stable key from road name
    key = generate_road_key(name)
    
    # Escape single quotes in name and key for SQL
    escaped_name = name.replace("'", "''")
    escaped_key = key.replace("'", "''")
    
    # Extract road type (use empty string if not present)
    road_type = road_data.get('road_type', '')
    escaped_type = road_type.replace("'", "''") if road_type else ''
    
    # Extract length (REAL)
    length = road_data.get('length', 0.0)
    
    # Extract size
    size = road_data.get('size', 'medium')
    escaped_size = size.replace("'", "''")
    
    # Extract areas and convert to IDs if mapping provided
    area_names = road_data.get('areas', [])
    if area_id_map:
        # Convert area names to IDs, keep unmapped names as-is for warning later
        area_ids = [area_id_map.get(area_name, area_name) for area_name in area_names]
    else:
        # Keep as names (for backward compatibility)
        area_ids = area_names
    
    areas_json = json.dumps(area_ids)
    escaped_areas = areas_json.replace("\\", "\\\\").replace("'", "''")
    
    # Extract sub_areas and convert to IDs if mapping provided
    sub_area_names = road_data.get('sub_areas', [])
    if sub_area_id_map:
        # Convert sub-area names to IDs, keep unmapped names as-is for warning later
        sub_area_ids = [sub_area_id_map.get(sub_area_name, sub_area_name) for sub_area_name in sub_area_names]
    else:
        # Keep as names (for backward compatibility)
        sub_area_ids = sub_area_names
    
    sub_area_ids_json = json.dumps(sub_area_ids)
    escaped_sub_area_ids = sub_area_ids_json.replace("\\", "\\\\").replace("'", "''")
    
    # Extract coordinates as JSON
    coordinates = road_data.get('coordinates', [])
    coordinates_json = json.dumps(coordinates)
    escaped_coordinates = coordinates_json.replace("\\", "\\\\").replace("'", "''")
    
    # Extract segments - create a JSON array of segment objects
    # The schema expects a JSON array of segment objects
    segments = []
    for i, coord_segment in enumerate(coordinates):
        segments.append({
            'index': i,
            'coordinates': coord_segment
        })
    segments_json = json.dumps(segments)
    escaped_segments = segments_json.replace("\\", "\\\\").replace("'", "''")
    
    # Build the field lists and values
    fields = ['key', 'district_id', 'name', 'length', 'size', 'segments', 'areas', 'coordinates', 'sub_area_ids']
    values = [
        f"'{escaped_key}'",
        str(district_id),
        f"'{escaped_name}'",
        str(length),
        f"'{escaped_size}'",
        f"'{escaped_segments}'",
        f"'{escaped_areas}'",
        f"'{escaped_coordinates}'",
        f"'{escaped_sub_area_ids}'"
    ]
    
    # Add type if it exists
    if road_type:
        fields.insert(4, 'type')
        values.insert(4, f"'{escaped_type}'")
    
    # Generate SQL query
    fields_str = ', '.join(fields)
    values_str = ', '.join(values)
    
    # Add comments about unmapped areas if needed
    unmapped_comment = ""
    unmapped_comment += generate_unmapped_warning(area_names, area_id_map, "areas")
    unmapped_comment += generate_unmapped_warning(sub_area_names, sub_area_id_map, "sub-areas")
    
    query = f"""{unmapped_comment}INSERT INTO roads ({fields_str})
VALUES ({values_str});"""
    
    return query


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description='Generate SQL INSERT queries for creating roads from formatted_roads.json'
    )
    parser.add_argument(
        '--district-id',
        type=int,
        default=None,
        help=f'District ID (default: {DISTRICT_ID})'
    )
    parser.add_argument(
        '--input',
        type=str,
        default=None,
        help=f'Path to formatted roads JSON file (default: {FORMATTED_ROADS_FILE})'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help=f'Output file path (default: {OUTPUT_FILE})'
    )
    parser.add_argument(
        '--area-mappings',
        type=str,
        default=None,
        help='Path to area mappings JSON file (optional)'
    )
    parser.add_argument(
        '--no-interactive',
        action='store_true',
        help='Disable interactive prompts for area ID mappings'
    )
    
    args = parser.parse_args()
    
    # Use command-line arguments if provided, otherwise use variables from top of file
    district_id = args.district_id if args.district_id is not None else DISTRICT_ID
    input_file = args.input if args.input is not None else FORMATTED_ROADS_FILE
    output_file = args.output if args.output is not None else OUTPUT_FILE
    mappings_file = args.area_mappings if args.area_mappings is not None else AREA_MAPPINGS_FILE
    interactive = not args.no_interactive
    
    # Get script directory for relative paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Make paths absolute if they're relative
    if not os.path.isabs(input_file):
        input_file = os.path.join(script_dir, input_file)
    if not os.path.isabs(output_file):
        output_file = os.path.join(script_dir, output_file)
    if mappings_file and not os.path.isabs(mappings_file):
        mappings_file = os.path.join(script_dir, mappings_file)
    
    # Load formatted roads
    print(f"Loading formatted roads from {input_file}...")
    formatted_roads = load_json_file(input_file)
    
    if formatted_roads is None:
        print("Error: Could not load formatted roads", file=sys.stderr)
        return 1
    
    if not isinstance(formatted_roads, dict):
        print("Error: Expected formatted_roads.json to contain a dictionary", file=sys.stderr)
        return 1
    
    # Load or create area ID mappings
    area_id_map, sub_area_id_map = load_or_create_area_mappings(
        formatted_roads, 
        mappings_file=mappings_file,
        interactive=interactive
    )
    
    # Generate SQL queries for each road
    queries = []
    for name, road_data in formatted_roads.items():
        try:
            query = generate_road_insert_query(
                district_id, 
                name, 
                road_data,
                area_id_map=area_id_map,
                sub_area_id_map=sub_area_id_map
            )
            queries.append(query)
        except ValueError as e:
            print(f"Error processing road '{name}': {e}", file=sys.stderr)
    
    print(f"\nGenerated {len(queries)} road queries")
    
    if not queries:
        print("No queries generated. Check that your formatted_roads.json contains valid data.", file=sys.stderr)
        return 1
    
    # Write all queries to output file
    try:
        with open(output_file, 'w') as f:
            for query in queries:
                f.write(query)
                f.write('\n\n')
        print(f"Successfully wrote {len(queries)} SQL queries to {output_file}")
        
        # Save area mappings if any were created
        if (area_id_map or sub_area_id_map) and interactive:
            mappings_output = os.path.join(script_dir, 'area_mappings.json')
            with open(mappings_output, 'w') as f:
                json.dump({
                    'areas': area_id_map,
                    'sub_areas': sub_area_id_map
                }, f, indent=2)
            print(f"Saved area mappings to {mappings_output}")
        
        return 0
    except IOError as e:
        print(f"Error: Could not write to {output_file}: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
