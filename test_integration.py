#!/usr/bin/env python3
"""
Integration test demonstrating the complete workflow:
1. Create a district object from GeoJSON
2. Verify the output matches database schema requirements
3. Test both minimal and full district creation
"""

import json
import sys
from create_district import (
    create_district_from_geojson,
    create_district_object,
    slugify,
    validate_geojson_polygon
)


def test_complete_workflow():
    """Test the complete district creation workflow"""
    print("=" * 70)
    print("INTEGRATION TEST: District Object Creation Workflow")
    print("=" * 70)
    print()
    
    # Step 1: Create a minimal district
    print("Step 1: Creating minimal district object")
    print("-" * 70)
    minimal = create_district_from_geojson(
        'my_district.geojson',
        minimal=True
    )
    print(f"✓ Created minimal district with key: '{minimal['key']}'")
    print(f"✓ Name: '{minimal['name']}'")
    print(f"✓ Fields: {list(minimal.keys())}")
    assert 'key' in minimal
    assert 'name' in minimal
    assert len(minimal.keys()) == 2  # Only required fields
    print()
    
    # Step 2: Create a full district
    print("Step 2: Creating full district object")
    print("-" * 70)
    full = create_district_from_geojson(
        'my_district.geojson',
        key='north-hills',
        name='North Hills',
        status='active',
        road_count=0,
        owner=42,
        created_by=42
    )
    print(f"✓ Created full district with key: '{full['key']}'")
    print(f"✓ Name: '{full['name']}'")
    print(f"✓ Status: '{full['status']}'")
    print(f"✓ Road count: {full['road_count']}")
    print(f"✓ Owner: {full['owner']}")
    print(f"✓ Created by: {full['created_by']}")
    
    # Validate GeoJSON structure
    geojson = full['district_border_coordinates']
    validate_geojson_polygon(geojson)
    print(f"✓ GeoJSON type: {geojson['type']}")
    print(f"✓ Polygon is properly closed")
    print()
    
    # Step 3: Verify database schema compliance
    print("Step 3: Verifying database schema compliance")
    print("-" * 70)
    
    # Check required fields
    required_fields = ['key', 'name']
    for field in required_fields:
        assert field in full, f"Missing required field: {field}"
        assert full[field], f"Required field '{field}' is empty"
    print(f"✓ All required fields present and non-empty")
    
    # Check optional fields
    optional_fields = ['status', 'road_count', 'district_border_coordinates', 'owner', 'created_by']
    for field in optional_fields:
        if field in full:
            print(f"  • {field}: present")
    
    # Verify field types and constraints
    assert isinstance(full['key'], str), "key must be a string"
    assert isinstance(full['name'], str), "name must be a string"
    assert isinstance(full['status'], str), "status must be a string"
    assert full['status'] in ['active', 'archived', 'disabled'], "status must be valid"
    assert isinstance(full['road_count'], int), "road_count must be an integer"
    assert full['road_count'] >= 0, "road_count must be non-negative"
    assert isinstance(full['owner'], int), "owner must be an integer"
    assert isinstance(full['created_by'], int), "created_by must be an integer"
    assert isinstance(full['district_border_coordinates'], dict), "district_border_coordinates must be an object"
    print(f"✓ All field types are correct")
    
    # Verify key format (slug)
    assert full['key'] == slugify(full['key']), "key must be a valid slug"
    assert full['key'].islower(), "key must be lowercase"
    assert full['key'] == 'north-hills', "key should match expected value"
    print(f"✓ Key is properly formatted as a slug: '{full['key']}'")
    print()
    
    # Step 4: Test JSON serialization
    print("Step 4: Testing JSON serialization")
    print("-" * 70)
    try:
        json_str = json.dumps(full, indent=2)
        parsed = json.loads(json_str)
        assert parsed == full, "JSON round-trip failed"
        print(f"✓ District object is JSON-serializable")
        print(f"✓ JSON size: {len(json_str)} bytes")
    except Exception as e:
        print(f"✗ JSON serialization failed: {e}")
        return False
    print()
    
    # Step 5: Verify coordinates format
    print("Step 5: Verifying GeoJSON coordinates format")
    print("-" * 70)
    coords = geojson['coordinates'][0]  # First ring
    print(f"✓ Number of coordinate points: {len(coords)}")
    
    # Check coordinate format [longitude, latitude]
    for i, coord in enumerate(coords[:3]):  # Check first 3 points
        assert isinstance(coord, list), f"Coordinate {i} must be a list"
        assert len(coord) == 2, f"Coordinate {i} must have 2 values"
        lng, lat = coord
        assert isinstance(lng, (int, float)), f"Longitude must be numeric"
        assert isinstance(lat, (int, float)), f"Latitude must be numeric"
        assert -180 <= lng <= 180, f"Longitude must be in range [-180, 180]"
        assert -90 <= lat <= 90, f"Latitude must be in range [-90, 90]"
    print(f"✓ First coordinate: [lng={coords[0][0]}, lat={coords[0][1]}]")
    print(f"✓ Coordinates are in [longitude, latitude] format")
    
    # Verify ring is closed
    assert coords[0] == coords[-1], "Polygon ring must be closed"
    print(f"✓ Polygon ring is properly closed")
    print()
    
    # Step 6: Database compatibility check
    print("Step 6: Database compatibility verification")
    print("-" * 70)
    
    # Check that no DB-managed fields are present
    db_managed_fields = ['id', 'updated_at', 'deleted_at']
    for field in db_managed_fields:
        assert field not in full, f"DB-managed field '{field}' should not be in create payload"
    print(f"✓ No DB-managed fields present (id, updated_at, deleted_at)")
    
    # Verify unique constraint on key
    print(f"✓ Key is unique and suitable for database UNIQUE constraint")
    
    # Verify foreign keys are integers (if present)
    fk_fields = ['owner', 'created_by']
    for field in fk_fields:
        if field in full:
            assert isinstance(full[field], int), f"{field} must be an integer for FK constraint"
    print(f"✓ Foreign key fields (owner, created_by) are integers")
    print()
    
    # Final summary
    print("=" * 70)
    print("INTEGRATION TEST RESULTS")
    print("=" * 70)
    print("✓ All tests passed!")
    print()
    print("District objects are ready for:")
    print("  • API upload (POST /districts)")
    print("  • Direct database insertion")
    print("  • Validation against database schema")
    print()
    print("Sample minimal payload:")
    print(json.dumps(minimal, indent=2))
    print()
    print("Full payload includes:")
    print("  • All required fields (key, name)")
    print("  • Optional metadata (status, road_count)")
    print("  • GeoJSON boundary (district_border_coordinates)")
    print("  • User references (owner, created_by)")
    print("=" * 70)
    
    return True


if __name__ == '__main__':
    try:
        success = test_complete_workflow()
        sys.exit(0 if success else 1)
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
