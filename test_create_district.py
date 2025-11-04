#!/usr/bin/env python3
"""
Test script for create_district.py
Tests district object creation and validation
"""

import json
import sys
from create_district import (
    slugify,
    validate_district_key,
    validate_district_name,
    validate_status,
    validate_geojson_polygon,
    create_district_object,
    create_district_from_geojson
)


def test_slugify():
    """Test slug generation from various inputs"""
    print("Testing slugify function...")
    
    test_cases = [
        ("North Hills", "north-hills"),
        ("Downtown District", "downtown-district"),
        ("Station-8", "station-8"),
        ("UPPER CASE", "upper-case"),
        ("With   Multiple    Spaces", "with-multiple-spaces"),
        ("Special!@#$%Characters", "specialcharacters"),
        ("Underscores_And_Dashes-Mixed", "underscores-and-dashes-mixed"),
        ("   Leading and Trailing   ", "leading-and-trailing"),
        ("Multiple---Dashes", "multiple-dashes"),
    ]
    
    all_passed = True
    for input_text, expected_slug in test_cases:
        actual_slug = slugify(input_text)
        if actual_slug == expected_slug:
            print(f"  ✓ '{input_text}' -> '{actual_slug}'")
        else:
            print(f"  ✗ '{input_text}' -> Expected '{expected_slug}', got '{actual_slug}'")
            all_passed = False
    
    if all_passed:
        print("✓ All slugify tests passed!\n")
        return True
    else:
        print("✗ Some slugify tests failed\n")
        return False


def test_validation_functions():
    """Test validation functions for district fields"""
    print("Testing validation functions...")
    
    # Test valid key
    try:
        validate_district_key("north-hills")
        print("  ✓ Valid district key accepted")
    except ValueError as e:
        print(f"  ✗ Valid key rejected: {e}")
        return False
    
    # Test invalid key (uppercase)
    try:
        validate_district_key("North-Hills")
        print("  ✗ Invalid key (uppercase) accepted")
        return False
    except ValueError:
        print("  ✓ Invalid key (uppercase) rejected")
    
    # Test invalid key (empty)
    try:
        validate_district_key("")
        print("  ✗ Empty key accepted")
        return False
    except ValueError:
        print("  ✓ Empty key rejected")
    
    # Test valid name
    try:
        validate_district_name("North Hills")
        print("  ✓ Valid district name accepted")
    except ValueError as e:
        print(f"  ✗ Valid name rejected: {e}")
        return False
    
    # Test invalid name (empty)
    try:
        validate_district_name("")
        print("  ✗ Empty name accepted")
        return False
    except ValueError:
        print("  ✓ Empty name rejected")
    
    # Test valid status
    try:
        validate_status("active")
        print("  ✓ Valid status 'active' accepted")
    except ValueError as e:
        print(f"  ✗ Valid status rejected: {e}")
        return False
    
    # Test invalid status
    try:
        validate_status("invalid")
        print("  ✗ Invalid status accepted")
        return False
    except ValueError:
        print("  ✓ Invalid status rejected")
    
    print("✓ All validation tests passed!\n")
    return True


def test_geojson_validation():
    """Test GeoJSON polygon validation"""
    print("Testing GeoJSON validation...")
    
    # Valid polygon
    valid_polygon = {
        "type": "Polygon",
        "coordinates": [
            [
                [-122.4231, 37.8268],
                [-122.4231, 37.8168],
                [-122.4131, 37.8168],
                [-122.4131, 37.8268],
                [-122.4231, 37.8268]  # Closed ring
            ]
        ]
    }
    
    try:
        validate_geojson_polygon(valid_polygon)
        print("  ✓ Valid polygon accepted")
    except ValueError as e:
        print(f"  ✗ Valid polygon rejected: {e}")
        return False
    
    # Invalid polygon (not closed)
    invalid_polygon = {
        "type": "Polygon",
        "coordinates": [
            [
                [-122.4231, 37.8268],
                [-122.4231, 37.8168],
                [-122.4131, 37.8168],
                [-122.4131, 37.8268]  # Missing closing coordinate
            ]
        ]
    }
    
    try:
        validate_geojson_polygon(invalid_polygon)
        print("  ✗ Invalid polygon (not closed) accepted")
        return False
    except ValueError:
        print("  ✓ Invalid polygon (not closed) rejected")
    
    # Invalid type
    invalid_type = {
        "type": "Point",
        "coordinates": [-122.4231, 37.8268]
    }
    
    try:
        validate_geojson_polygon(invalid_type)
        print("  ✗ Invalid type (Point) accepted")
        return False
    except ValueError:
        print("  ✓ Invalid type (Point) rejected")
    
    print("✓ All GeoJSON validation tests passed!\n")
    return True


def test_minimal_district_creation():
    """Test creating a minimal district object"""
    print("Testing minimal district creation...")
    
    district = create_district_object(
        key="north-hills",
        name="North Hills",
        minimal=True
    )
    
    # Check that only required fields are present
    expected_keys = {"key", "name"}
    actual_keys = set(district.keys())
    
    if actual_keys == expected_keys:
        print("  ✓ Minimal district has only required fields")
    else:
        print(f"  ✗ Expected keys {expected_keys}, got {actual_keys}")
        return False
    
    # Check field values
    if district["key"] == "north-hills" and district["name"] == "North Hills":
        print("  ✓ Field values are correct")
    else:
        print(f"  ✗ Field values incorrect: {district}")
        return False
    
    print("✓ Minimal district creation test passed!\n")
    return True


def test_full_district_creation():
    """Test creating a full district object"""
    print("Testing full district creation...")
    
    polygon = {
        "type": "Polygon",
        "coordinates": [
            [
                [-122.4231, 37.8268],
                [-122.4231, 37.8168],
                [-122.4131, 37.8168],
                [-122.4131, 37.8268],
                [-122.4231, 37.8268]
            ]
        ]
    }
    
    district = create_district_object(
        key="north-hills",
        name="North Hills",
        status="active",
        road_count=0,
        district_border_coordinates=polygon,
        owner=42,
        created_by=42
    )
    
    # Check that all expected fields are present
    expected_keys = {
        "key", "name", "status", "road_count",
        "district_border_coordinates", "owner", "created_by"
    }
    actual_keys = set(district.keys())
    
    if actual_keys == expected_keys:
        print("  ✓ Full district has all expected fields")
    else:
        missing = expected_keys - actual_keys
        extra = actual_keys - expected_keys
        if missing:
            print(f"  ✗ Missing fields: {missing}")
        if extra:
            print(f"  ✗ Extra fields: {extra}")
        return False
    
    # Check field values
    if (district["key"] == "north-hills" and 
        district["name"] == "North Hills" and
        district["status"] == "active" and
        district["road_count"] == 0 and
        district["owner"] == 42 and
        district["created_by"] == 42):
        print("  ✓ Field values are correct")
    else:
        print(f"  ✗ Field values incorrect")
        return False
    
    # Check GeoJSON structure
    if district["district_border_coordinates"]["type"] == "Polygon":
        print("  ✓ GeoJSON polygon is present")
    else:
        print(f"  ✗ GeoJSON type incorrect")
        return False
    
    print("✓ Full district creation test passed!\n")
    return True


def test_create_from_geojson():
    """Test creating district from GeoJSON file"""
    print("Testing district creation from GeoJSON file...")
    
    try:
        # Test with my_district.geojson
        district = create_district_from_geojson(
            'my_district.geojson',
            key='test-district',
            name='Test District',
            status='active',
            road_count=0
        )
        
        # Check required fields
        if district["key"] != "test-district":
            print(f"  ✗ Key mismatch: expected 'test-district', got '{district['key']}'")
            return False
        
        if district["name"] != "Test District":
            print(f"  ✗ Name mismatch: expected 'Test District', got '{district['name']}'")
            return False
        
        # Check GeoJSON is loaded
        if "district_border_coordinates" not in district:
            print("  ✗ district_border_coordinates not found")
            return False
        
        if district["district_border_coordinates"]["type"] not in ["Polygon", "MultiPolygon"]:
            print(f"  ✗ Invalid GeoJSON type: {district['district_border_coordinates']['type']}")
            return False
        
        print("  ✓ District created successfully from GeoJSON file")
        print("  ✓ All expected fields present and valid")
        
        # Test auto-generation of key and name
        auto_district = create_district_from_geojson(
            'my_district.geojson',
            minimal=True
        )
        
        if auto_district["key"] and auto_district["name"]:
            print(f"  ✓ Auto-generated key: '{auto_district['key']}'")
            print(f"  ✓ Auto-generated name: '{auto_district['name']}'")
        else:
            print("  ✗ Auto-generation failed")
            return False
        
    except FileNotFoundError:
        print("  ⚠ my_district.geojson not found, skipping file-based test")
        return True
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False
    
    print("✓ GeoJSON file creation test passed!\n")
    return True


def test_error_handling():
    """Test error handling for invalid inputs"""
    print("Testing error handling...")
    
    # Test invalid road_count
    try:
        create_district_object(
            key="test",
            name="Test",
            road_count=-1
        )
        print("  ✗ Negative road_count accepted")
        return False
    except ValueError:
        print("  ✓ Negative road_count rejected")
    
    # Test invalid owner type
    try:
        create_district_object(
            key="test",
            name="Test",
            owner="not-an-integer"
        )
        print("  ✗ Non-integer owner accepted")
        return False
    except ValueError:
        print("  ✓ Non-integer owner rejected")
    
    # Test invalid created_by type
    try:
        create_district_object(
            key="test",
            name="Test",
            created_by=3.14
        )
        print("  ✗ Non-integer created_by accepted")
        return False
    except ValueError:
        print("  ✓ Non-integer created_by rejected")
    
    print("✓ All error handling tests passed!\n")
    return True


def main():
    """Run all tests"""
    print("=" * 60)
    print("Running District Creation Tests")
    print("=" * 60 + "\n")
    
    results = []
    
    results.append(("Slugify", test_slugify()))
    results.append(("Validation", test_validation_functions()))
    results.append(("GeoJSON Validation", test_geojson_validation()))
    results.append(("Minimal District", test_minimal_district_creation()))
    results.append(("Full District", test_full_district_creation()))
    results.append(("GeoJSON File", test_create_from_geojson()))
    results.append(("Error Handling", test_error_handling()))
    
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{test_name:.<40} {status}")
    
    print("-" * 60)
    print(f"Total: {passed}/{total} tests passed")
    print("=" * 60)
    
    if passed == total:
        print("\n✓ All tests passed!")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())
