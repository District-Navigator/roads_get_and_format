#!/usr/bin/env python3
"""
Program 4: Create District Object
Creates a district object that matches the database schema requirements.
The output can be used to create districts via API or direct database insertion.
"""

import json
import re
from pathlib import Path
from datetime import datetime


def slugify(text):
    """
    Convert text to a URL-safe slug format.
    
    Args:
        text: The text to convert to a slug
        
    Returns:
        str: URL-safe slug (lowercase, alphanumeric with hyphens)
    """
    # Convert to lowercase
    text = text.lower()
    # Replace spaces and underscores with hyphens
    text = re.sub(r'[\s_]+', '-', text)
    # Remove non-alphanumeric characters except hyphens
    text = re.sub(r'[^a-z0-9\-]', '', text)
    # Remove multiple consecutive hyphens
    text = re.sub(r'-+', '-', text)
    # Remove leading/trailing hyphens
    text = text.strip('-')
    return text


def validate_district_key(key):
    """
    Validate that a district key is properly formatted.
    
    Args:
        key: The district key to validate
        
    Returns:
        bool: True if valid, raises ValueError otherwise
    """
    if not key:
        raise ValueError("District key cannot be empty")
    
    if len(key) > 255:
        raise ValueError("District key must be 255 characters or less")
    
    # Check for valid slug format (lowercase letters, numbers, hyphens)
    if not re.match(r'^[a-z0-9\-]+$', key):
        raise ValueError(
            "District key must contain only lowercase letters, numbers, and hyphens"
        )
    
    return True


def validate_district_name(name):
    """
    Validate that a district name is properly formatted.
    
    Args:
        name: The district name to validate
        
    Returns:
        bool: True if valid, raises ValueError otherwise
    """
    if not name:
        raise ValueError("District name cannot be empty")
    
    if len(name) > 255:
        raise ValueError("District name must be 255 characters or less")
    
    return True


def validate_status(status):
    """
    Validate that status is one of the allowed values.
    
    Args:
        status: The status value to validate
        
    Returns:
        bool: True if valid, raises ValueError otherwise
    """
    allowed_statuses = ['active', 'archived', 'disabled']
    if status and status not in allowed_statuses:
        raise ValueError(
            f"Status must be one of {allowed_statuses}, got '{status}'"
        )
    return True


def validate_geojson_polygon(geojson_obj):
    """
    Validate that a GeoJSON object is a valid Polygon or MultiPolygon.
    
    Args:
        geojson_obj: The GeoJSON object to validate
        
    Returns:
        bool: True if valid, raises ValueError otherwise
    """
    if not isinstance(geojson_obj, dict):
        raise ValueError("GeoJSON must be a dictionary object")
    
    if 'type' not in geojson_obj:
        raise ValueError("GeoJSON must have a 'type' field")
    
    if geojson_obj['type'] not in ['Polygon', 'MultiPolygon']:
        raise ValueError(
            f"GeoJSON type must be 'Polygon' or 'MultiPolygon', got '{geojson_obj['type']}'"
        )
    
    if 'coordinates' not in geojson_obj:
        raise ValueError("GeoJSON must have a 'coordinates' field")
    
    # Validate polygon ring closure for Polygon
    if geojson_obj['type'] == 'Polygon':
        for ring in geojson_obj['coordinates']:
            if len(ring) < 4:
                raise ValueError("Polygon ring must have at least 4 coordinates")
            # Check that first and last coordinates are equal (ring is closed)
            if ring[0] != ring[-1]:
                raise ValueError(
                    "Polygon ring must be closed (first and last coordinates must be equal)"
                )
    
    return True


def load_geojson_file(geojson_file):
    """
    Load a GeoJSON file and extract the polygon geometry.
    Automatically converts MultiLineString to Polygon if the line is closed.
    
    Args:
        geojson_file: Path to the GeoJSON file
        
    Returns:
        dict: GeoJSON Polygon or MultiPolygon object
    """
    with open(geojson_file, 'r') as f:
        geojson_data = json.load(f)
    
    # Extract geometry from GeoJSON
    if geojson_data['type'] == 'FeatureCollection':
        if not geojson_data.get('features'):
            raise ValueError("FeatureCollection has no features")
        geometry = geojson_data['features'][0]['geometry']
    elif geojson_data['type'] == 'Feature':
        geometry = geojson_data['geometry']
    else:
        # Assume it's already a geometry object
        geometry = geojson_data
    
    # Convert MultiLineString to Polygon if it's a closed loop
    if geometry['type'] == 'MultiLineString':
        # MultiLineString with one line that forms a closed loop -> Polygon
        if len(geometry['coordinates']) == 1:
            line_coords = geometry['coordinates'][0]
            # Check if it's closed (first point equals last point)
            if line_coords[0] == line_coords[-1]:
                # Convert to Polygon
                geometry = {
                    'type': 'Polygon',
                    'coordinates': [line_coords]
                }
            else:
                raise ValueError(
                    "MultiLineString must be closed (first point = last point) to convert to Polygon"
                )
        else:
            raise ValueError(
                "MultiLineString with multiple lines cannot be converted to Polygon"
            )
    
    return geometry


def create_district_object(
    key,
    name,
    status=None,
    road_count=None,
    district_border_coordinates=None,
    owner=None,
    created_by=None,
    created_at=None,
    minimal=False
):
    """
    Create a district object following the database schema.
    
    Args:
        key: Unique district slug (required)
        name: Human-readable district name (required)
        status: District status ('active', 'archived', 'disabled')
        road_count: Number of roads in the district
        district_border_coordinates: GeoJSON Polygon or MultiPolygon object
        owner: Owner user ID (integer or None)
        created_by: Creator user ID (integer or None)
        created_at: Creation timestamp (ISO 8601 string)
        minimal: If True, only include required fields
        
    Returns:
        dict: District object matching database schema
    """
    # Validate required fields
    validate_district_key(key)
    validate_district_name(name)
    
    # Create the minimal district object
    district = {
        "key": key,
        "name": name
    }
    
    # If minimal mode, return only required fields
    if minimal:
        return district
    
    # Add optional fields if provided
    if status is not None:
        validate_status(status)
        district["status"] = status
    
    if road_count is not None:
        # Explicitly reject boolean values (bool is subclass of int in Python)
        if isinstance(road_count, bool) or not isinstance(road_count, int):
            raise ValueError("road_count must be a non-negative integer")
        if road_count < 0:
            raise ValueError("road_count must be a non-negative integer")
        district["road_count"] = road_count
    
    if district_border_coordinates is not None:
        validate_geojson_polygon(district_border_coordinates)
        district["district_border_coordinates"] = district_border_coordinates
    
    if owner is not None:
        if not isinstance(owner, int):
            raise ValueError("owner must be an integer (user ID)")
        district["owner"] = owner
    
    if created_by is not None:
        if not isinstance(created_by, int):
            raise ValueError("created_by must be an integer (user ID)")
        district["created_by"] = created_by
    
    if created_at is not None:
        # Validate ISO 8601 format
        try:
            datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        except ValueError:
            raise ValueError(
                f"created_at must be a valid ISO 8601 timestamp, got '{created_at}'"
            )
        district["created_at"] = created_at
    
    return district


def create_district_from_geojson(
    geojson_file,
    key=None,
    name=None,
    status='active',
    road_count=0,
    owner=None,
    created_by=None,
    minimal=False
):
    """
    Create a district object from a GeoJSON file.
    
    Convenience function that loads the district boundary from a GeoJSON file
    and creates a district object with it.
    
    Args:
        geojson_file: Path to GeoJSON file containing district boundary
        key: Unique district slug (auto-generated from name if not provided)
        name: Human-readable district name (auto-generated from filename if not provided)
        status: District status ('active', 'archived', 'disabled')
        road_count: Number of roads in the district
        owner: Owner user ID (integer or None)
        created_by: Creator user ID (integer or None)
        minimal: If True, only include required fields
        
    Returns:
        dict: District object matching database schema
    """
    # Load the GeoJSON polygon
    polygon = load_geojson_file(geojson_file)
    
    # Auto-generate name from filename if not provided
    if name is None:
        # Get filename without extension (e.g., "my_district.geojson" -> "my_district")
        file_stem = Path(geojson_file).stem
        # Convert to human-readable name (e.g., "my_district" -> "My District")
        name = file_stem.replace('_', ' ').replace('-', ' ').title()
    
    # Auto-generate key from name if not provided
    if key is None:
        key = slugify(name)
    
    # Create the district object
    return create_district_object(
        key=key,
        name=name,
        status=status if not minimal else None,
        road_count=road_count if not minimal else None,
        district_border_coordinates=polygon if not minimal else None,
        owner=owner,
        created_by=created_by,
        minimal=minimal
    )


def save_district_object(district, output_file):
    """
    Save a district object to a JSON file.
    
    Args:
        district: District object dictionary
        output_file: Path to output JSON file
    """
    with open(output_file, 'w') as f:
        json.dump(district, f, indent=2)
    
    print(f"Saved district object to {output_file}")


def main():
    """Main execution function."""
    # Example: Create a district from my_district.geojson
    geojson_file = 'my_district.geojson'
    
    print(f"Creating district object from {geojson_file}...")
    
    # Create a minimal district object
    print("\n--- Creating minimal district object ---")
    minimal_district = create_district_from_geojson(
        geojson_file,
        minimal=True
    )
    print("Minimal district object:")
    print(json.dumps(minimal_district, indent=2))
    save_district_object(minimal_district, 'district_minimal.json')
    
    # Create a full district object
    print("\n--- Creating full district object ---")
    full_district = create_district_from_geojson(
        geojson_file,
        status='active',
        road_count=0,
        owner=42,
        created_by=42
    )
    print("Full district object:")
    print(json.dumps(full_district, indent=2))
    save_district_object(full_district, 'district_full.json')
    
    print("\nDone!")


if __name__ == '__main__':
    main()
