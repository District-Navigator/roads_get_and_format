#!/usr/bin/env python3
"""
Create District SQL Query Generator
Generates SQL INSERT queries for adding districts to the database.
Takes inputs: name, created_at, created_by, district_border_coordinates, owner
"""

import argparse
import json
import os
import sys

# ============================================================================
# INPUT VARIABLES - Edit these values when running in PyCharm/IDE
# ============================================================================
DISTRICT_NAME = "My District"
CREATED_AT = None  # Use None for datetime('now'), or provide ISO8601 string like '2025-01-15 12:00:00'
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


def generate_district_insert_query(name, created_at, created_by, district_border_coordinates, owner):
    """
    Generate an SQL INSERT query for adding a district to the database.
    
    Args:
        name: District name (TEXT, required)
        created_at: Created timestamp (TEXT ISO8601 string or None for datetime('now'))
        created_by: User ID who created the district (INTEGER, FK to users.id)
        district_border_coordinates: GeoJSON geometry as JSON string (TEXT or None)
        owner: Owner user ID (INTEGER, FK to users.id)
        
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
    escaped_name = name.replace("'", "''")
    
    # Build the field lists and values
    fields = ['name', 'created_by', 'owner']
    values = [f"'{escaped_name}'", str(created_by), str(owner)]
    
    # Add created_at if provided
    if created_at is not None:
        # Escape single quotes in timestamp string
        # Note: created_at should be a string in ISO8601 format like '2025-01-15 12:00:00'
        escaped_created_at = str(created_at).replace("'", "''")
        fields.append('created_at')
        values.append(f"'{escaped_created_at}'")
    
    # Add district_border_coordinates if provided
    if district_border_coordinates is not None:
        # Escape single quotes and backslashes in JSON string for SQL
        # Double backslashes first to prevent double-escaping, then escape quotes
        escaped_coordinates = str(district_border_coordinates).replace("\\", "\\\\").replace("'", "''")
        fields.append('district_border_coordinates')
        values.append(f"'{escaped_coordinates}'")
    
    # Generate SQL query
    fields_str = ', '.join(fields)
    values_str = ', '.join(values)
    query = f"""INSERT INTO districts ({fields_str})
VALUES ({values_str});"""
    
    return query


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description='Generate SQL INSERT query for adding a district'
    )
    parser.add_argument(
        'name',
        type=str,
        nargs='?',
        default=None,
        help='District name'
    )
    parser.add_argument(
        'created_at',
        type=str,
        nargs='?',
        default=None,
        help='Created timestamp (ISO8601 format, or omit for datetime(\'now\'))'
    )
    parser.add_argument(
        'created_by',
        type=int,
        nargs='?',
        default=None,
        help='User ID of the creator (FK to users.id)'
    )
    parser.add_argument(
        'owner',
        type=int,
        nargs='?',
        default=None,
        help='User ID of the owner (FK to users.id)'
    )
    parser.add_argument(
        '--geojson',
        type=str,
        default='my_district.geojson',
        help='Path to GeoJSON file (default: my_district.geojson)'
    )
    
    args = parser.parse_args()
    
    # Use command-line arguments if provided, otherwise use variables from top of file
    name = args.name if args.name is not None else DISTRICT_NAME
    # Treat empty strings as None for optional fields
    created_at = args.created_at if args.created_at not in (None, '') else CREATED_AT
    created_by = args.created_by if args.created_by is not None else CREATED_BY
    owner = args.owner if args.owner is not None else OWNER
    
    # Load coordinates from GeoJSON file
    # Use absolute path if provided, otherwise look in script directory
    geojson_path = args.geojson
    if not os.path.isabs(geojson_path):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        geojson_path = os.path.join(script_dir, geojson_path)
    district_border_coordinates = load_coordinates_from_geojson(geojson_path)
    
    try:
        query = generate_district_insert_query(name, created_at, created_by, district_border_coordinates, owner)
        print(query)
        return 0
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
