#!/usr/bin/env python3
"""
Create District SQL Query Generator
Generates SQL INSERT queries for adding districts to the database.
Takes inputs: name, created_by, owner
"""

import argparse
import json
import os
import sys

# ============================================================================
# INPUT VARIABLES - Edit these values when running in PyCharm/IDE
# ============================================================================
DISTRICT_NAME = "Berea SC"
CREATED_BY = 1
OWNER = 1
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


def generate_district_insert_query(name, created_by, owner, coordinates=None):
    """
    Generate an SQL INSERT query for adding a district to the database.
    
    Args:
        name: District name (TEXT, required)
        created_by: User ID who created the district (INTEGER, FK to users.id)
        owner: Owner user ID (INTEGER, FK to users.id)
        coordinates: GeoJSON geometry string (optional)
        
    Returns:
        str: SQL INSERT query
    """
    # Validate inputs
    if not name or not name.strip():
        raise ValueError("District name cannot be empty")
    
    if not isinstance(created_by, int):
        try:
            created_by = int(created_by)
        except (ValueError, TypeError):
            raise ValueError("created_by must be an integer (user ID)")
    
    if not isinstance(owner, int):
        try:
            owner = int(owner)
        except (ValueError, TypeError):
            raise ValueError("owner must be an integer (user ID)")
    
    # Escape single quotes in name for SQL (SQLite standard: '' escapes ')
    # Note: This is the standard SQL escape mechanism for single quotes.
    # For production use with user input from untrusted sources, consider using
    # parameterized queries via a database library (e.g., sqlite3 with placeholders).
    escaped_name = name.replace("'", "''")
    
    # Generate SQL query
    # The database schema has defaults for status, road_count, created_at, updated_at
    # We now include district_border_coordinates if available
    if coordinates:
        # Escape single quotes in JSON string for SQL
        escaped_coordinates = coordinates.replace("'", "''")
        query = f"""INSERT INTO districts (name, created_by, owner, district_border_coordinates)
VALUES ('{escaped_name}', {created_by}, {owner}, '{escaped_coordinates}');"""
    else:
        query = f"""INSERT INTO districts (name, created_by, owner)
VALUES ('{escaped_name}', {created_by}, {owner});"""
    
    return query


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description='Generate SQL INSERT query for creating a district'
    )
    parser.add_argument(
        'name',
        type=str,
        nargs='?',  # Make positional argument optional
        default=None,
        help='District name'
    )
    parser.add_argument(
        'created_by',
        type=int,
        nargs='?',  # Make positional argument optional
        default=None,
        help='User ID of the creator (FK to users.id)'
    )
    parser.add_argument(
        'owner',
        type=int,
        nargs='?',  # Make positional argument optional
        default=None,
        help='User ID of the owner (FK to users.id)'
    )
    
    args = parser.parse_args()
    
    # Use command-line arguments if provided, otherwise use variables from top of file
    name = args.name if args.name is not None else DISTRICT_NAME
    created_by = args.created_by if args.created_by is not None else CREATED_BY
    owner = args.owner if args.owner is not None else OWNER
    
    # Load coordinates from my_district.geojson
    script_dir = os.path.dirname(os.path.abspath(__file__))
    geojson_path = os.path.join(script_dir, 'my_district.geojson')
    coordinates = load_coordinates_from_geojson(geojson_path)
    
    try:
        query = generate_district_insert_query(name, created_by, owner, coordinates)
        print(query)
        return 0
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
