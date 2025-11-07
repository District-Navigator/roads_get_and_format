#!/usr/bin/env python3
"""
Create Areas SQL Query Generator
Generates SQL INSERT queries for adding areas and sub-areas to the database.
Reads from areas/ and sub_areas/ directories and creates SQL statements with coordinates.
"""

import argparse
import json
import os
import sys
from pathlib import Path

# ============================================================================
# INPUT VARIABLES - Edit these values when running in PyCharm/IDE
# ============================================================================
DISTRICT_ID = 1
CREATED_BY = 1
AREAS_DIR = "areas"
SUB_AREAS_DIR = "sub_areas"
OUTPUT_FILE = "step_5_output.txt"
# ============================================================================


def load_coordinates_from_geojson(geojson_path):
    """
    Load coordinates from a GeoJSON file.
    
    Args:
        geojson_path: Path to the GeoJSON file
        
    Returns:
        str: JSON string of the geometry object, or None if not found
    """
    try:
        with open(geojson_path, 'r') as f:
            geojson_data = json.load(f)
        
        # Extract geometry from the first feature
        if 'features' in geojson_data and len(geojson_data['features']) > 0:
            geometry = geojson_data['features'][0].get('geometry')
            if geometry:
                # Return the geometry as a JSON string
                return json.dumps(geometry)
    except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
        print(f"Warning: Could not load coordinates from {geojson_path}: {e}", file=sys.stderr)
    
    return None


def extract_area_name_from_filename(filename):
    """
    Extract area name from filename (e.g., 'station-10.geojson' -> 'station-10')
    
    Args:
        filename: Name of the GeoJSON file
        
    Returns:
        str: Area name without extension
    """
    return Path(filename).stem


def generate_area_insert_query(district_id, name, coordinates, sub_area, created_by):
    """
    Generate an SQL INSERT query for adding an area to the database.
    
    Args:
        district_id: District ID (INTEGER, FK to districts.id)
        name: Area name (TEXT, required)
        coordinates: GeoJSON geometry string (TEXT or None)
        sub_area: Boolean flag indicating if this is a sub-area (0 or 1)
        created_by: User ID who created the area (INTEGER, FK to users.id)
        
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
        raise ValueError("Area name cannot be empty")
    
    if not isinstance(created_by, int):
        try:
            created_by = int(created_by)
        except (ValueError, TypeError):
            raise ValueError("created_by must be an integer (user ID)")
    
    if not isinstance(sub_area, int) or sub_area not in (0, 1):
        raise ValueError("sub_area must be 0 or 1")
    
    # Escape single quotes in name for SQL
    escaped_name = name.replace("'", "''")
    
    # Build the field lists and values
    fields = ['district_id', 'name', 'sub_area', 'created_by']
    values = [str(district_id), f"'{escaped_name}'", str(sub_area), str(created_by)]
    
    # Add area_border_coordinates if provided
    if coordinates is not None:
        # Escape single quotes and backslashes in JSON string for SQL
        escaped_coordinates = str(coordinates).replace("\\", "\\\\").replace("'", "''")
        fields.append('area_border_coordinates')
        values.append(f"'{escaped_coordinates}'")
    
    # Generate SQL query
    fields_str = ', '.join(fields)
    values_str = ', '.join(values)
    query = f"""INSERT INTO areas ({fields_str})
VALUES ({values_str});"""
    
    return query


def process_area_files(areas_dir, district_id, created_by, is_sub_area=False):
    """
    Process all GeoJSON files in a directory and generate SQL INSERT queries.
    
    Args:
        areas_dir: Path to directory containing GeoJSON files
        district_id: District ID for all areas
        created_by: User ID who created the areas
        is_sub_area: Boolean indicating if these are sub-areas
        
    Returns:
        list: List of SQL INSERT queries
    """
    queries = []
    
    # Check if directory exists
    if not os.path.exists(areas_dir):
        print(f"Warning: Directory {areas_dir} does not exist", file=sys.stderr)
        return queries
    
    # Find all .geojson files in the directory
    geojson_files = sorted([f for f in os.listdir(areas_dir) if f.endswith('.geojson')])
    
    if not geojson_files:
        print(f"Warning: No .geojson files found in {areas_dir}", file=sys.stderr)
        return queries
    
    # Process each file
    for filename in geojson_files:
        filepath = os.path.join(areas_dir, filename)
        area_name = extract_area_name_from_filename(filename)
        coordinates = load_coordinates_from_geojson(filepath)
        
        if coordinates:
            try:
                query = generate_area_insert_query(
                    district_id,
                    area_name,
                    coordinates,
                    1 if is_sub_area else 0,
                    created_by
                )
                queries.append(query)
            except ValueError as e:
                print(f"Error processing {filename}: {e}", file=sys.stderr)
        else:
            print(f"Warning: No coordinates found in {filename}", file=sys.stderr)
    
    return queries


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description='Generate SQL INSERT queries for creating areas and sub-areas'
    )
    parser.add_argument(
        '--district-id',
        type=int,
        default=None,
        help=f'District ID (default: {DISTRICT_ID})'
    )
    parser.add_argument(
        '--created-by',
        type=int,
        default=None,
        help=f'User ID of the creator (default: {CREATED_BY})'
    )
    parser.add_argument(
        '--areas-dir',
        type=str,
        default=None,
        help=f'Path to areas directory (default: {AREAS_DIR})'
    )
    parser.add_argument(
        '--sub-areas-dir',
        type=str,
        default=None,
        help=f'Path to sub-areas directory (default: {SUB_AREAS_DIR})'
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
    created_by = args.created_by if args.created_by is not None else CREATED_BY
    areas_dir = args.areas_dir if args.areas_dir is not None else AREAS_DIR
    sub_areas_dir = args.sub_areas_dir if args.sub_areas_dir is not None else SUB_AREAS_DIR
    output_file = args.output if args.output is not None else OUTPUT_FILE
    
    # Get script directory for relative paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Make paths absolute if they're relative
    if not os.path.isabs(areas_dir):
        areas_dir = os.path.join(script_dir, areas_dir)
    if not os.path.isabs(sub_areas_dir):
        sub_areas_dir = os.path.join(script_dir, sub_areas_dir)
    if not os.path.isabs(output_file):
        output_file = os.path.join(script_dir, output_file)
    
    # Process areas
    print(f"Processing areas from {areas_dir}...")
    area_queries = process_area_files(areas_dir, district_id, created_by, is_sub_area=False)
    print(f"Generated {len(area_queries)} area queries")
    
    # Process sub-areas
    print(f"Processing sub-areas from {sub_areas_dir}...")
    sub_area_queries = process_area_files(sub_areas_dir, district_id, created_by, is_sub_area=True)
    print(f"Generated {len(sub_area_queries)} sub-area queries")
    
    # Combine all queries
    all_queries = area_queries + sub_area_queries
    
    if not all_queries:
        print("No queries generated. Check that your areas directories contain valid GeoJSON files.", file=sys.stderr)
        return 1
    
    # Write all queries to output file
    try:
        with open(output_file, 'w') as f:
            for query in all_queries:
                f.write(query)
                f.write('\n\n')
        print(f"\nSuccessfully wrote {len(all_queries)} SQL queries to {output_file}")
        return 0
    except IOError as e:
        print(f"Error: Could not write to {output_file}: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
