#!/usr/bin/env python3
"""
Create Roads SQL Query Generator
Generates SQL INSERT queries for adding roads to the database.
Reads from formatted_roads.json and creates SQL statements with coordinates.
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


def generate_road_insert_query(district_id, name, road_data):
    """
    Generate an SQL INSERT query for adding a road to the database.
    
    Note: The 'areas' field in the database expects a JSON array of area IDs (integers),
    but formatted_roads.json contains area names (strings). This function stores area
    names in the JSON for now. You should either:
    1. Post-process the SQL to replace area names with IDs after areas are created, OR
    2. Run a separate UPDATE query after inserting roads to populate area IDs, OR
    3. Have your application resolve area names to IDs before insertion
    
    Args:
        district_id: District ID (INTEGER, FK to districts.id)
        name: Road name (TEXT, required)
        road_data: Road data from formatted_roads.json
        
    Returns:
        str: SQL INSERT query with a comment about area name references
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
    
    # Extract areas as JSON array
    areas = road_data.get('areas', [])
    areas_json = json.dumps(areas)
    escaped_areas = areas_json.replace("\\", "\\\\").replace("'", "''")
    
    # Extract sub_areas - check if the list is non-empty
    sub_areas_list = road_data.get('sub_areas', [])
    sub_areas = 1 if sub_areas_list else 0
    
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
    fields = ['key', 'district_id', 'name', 'length', 'size', 'segments', 'areas', 'coordinates', 'sub_areas']
    values = [
        f"'{escaped_key}'",
        str(district_id),
        f"'{escaped_name}'",
        str(length),
        f"'{escaped_size}'",
        f"'{escaped_segments}'",
        f"'{escaped_areas}'",
        f"'{escaped_coordinates}'",
        str(sub_areas)
    ]
    
    # Add type if it exists
    if road_type:
        fields.insert(4, 'type')
        values.insert(4, f"'{escaped_type}'")
    
    # Generate SQL query with comment about area references
    fields_str = ', '.join(fields)
    values_str = ', '.join(values)
    
    # Add comment if there are area references
    area_comment = ""
    if areas:
        area_names = ', '.join(areas)
        area_comment = f"-- Road references areas: {area_names}\n-- Note: 'areas' field contains area names (strings) but schema expects area IDs (integers)\n-- You may need to replace these with actual area IDs after areas table is populated\n"
    
    query = f"""{area_comment}INSERT INTO roads ({fields_str})
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
    
    args = parser.parse_args()
    
    # Use command-line arguments if provided, otherwise use variables from top of file
    district_id = args.district_id if args.district_id is not None else DISTRICT_ID
    input_file = args.input if args.input is not None else FORMATTED_ROADS_FILE
    output_file = args.output if args.output is not None else OUTPUT_FILE
    
    # Get script directory for relative paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Make paths absolute if they're relative
    if not os.path.isabs(input_file):
        input_file = os.path.join(script_dir, input_file)
    if not os.path.isabs(output_file):
        output_file = os.path.join(script_dir, output_file)
    
    # Load formatted roads
    print(f"Loading formatted roads from {input_file}...")
    formatted_roads = load_json_file(input_file)
    
    if formatted_roads is None:
        print("Error: Could not load formatted roads", file=sys.stderr)
        return 1
    
    if not isinstance(formatted_roads, dict):
        print("Error: Expected formatted_roads.json to contain a dictionary", file=sys.stderr)
        return 1
    
    # Generate SQL queries for each road
    queries = []
    for name, road_data in formatted_roads.items():
        try:
            query = generate_road_insert_query(district_id, name, road_data)
            queries.append(query)
        except ValueError as e:
            print(f"Error processing road '{name}': {e}", file=sys.stderr)
    
    print(f"Generated {len(queries)} road queries")
    
    if not queries:
        print("No queries generated. Check that your formatted_roads.json contains valid data.", file=sys.stderr)
        return 1
    
    # Write all queries to output file
    try:
        with open(output_file, 'w') as f:
            for query in queries:
                f.write(query)
                f.write('\n\n')
        print(f"\nSuccessfully wrote {len(queries)} SQL queries to {output_file}")
        return 0
    except IOError as e:
        print(f"Error: Could not write to {output_file}: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
