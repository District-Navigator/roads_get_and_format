#!/usr/bin/env python3
"""
Test script for add_areas.py to verify area assignment functionality
"""
import json
import sys
import os
import tempfile
from pathlib import Path
from add_areas import load_area_geojson, load_all_areas, check_road_in_area, add_areas_to_roads


def test_load_area_geojson():
    """Test loading a GeoJSON area file"""
    print("Testing load_area_geojson...")
    
    # Create a temporary GeoJSON file
    test_geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [-82.5, 34.9],
                        [-82.4, 34.9],
                        [-82.4, 34.8],
                        [-82.5, 34.8],
                        [-82.5, 34.9]
                    ]]
                }
            }
        ]
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.geojson', delete=False) as f:
        json.dump(test_geojson, f)
        temp_file = f.name
    
    try:
        area_name, polygon = load_area_geojson(temp_file)
        
        if area_name and polygon:
            print(f"  ✓ Loaded area successfully")
            return True
        else:
            print(f"  ✗ Failed to load area")
            return False
    finally:
        os.unlink(temp_file)


def test_check_road_in_area():
    """Test checking if a road is within an area"""
    print("\nTesting check_road_in_area...")
    
    from shapely.geometry import Polygon
    
    # Create a test polygon (square from -82.5 to -82.4, 34.8 to 34.9)
    polygon = Polygon([
        [-82.5, 34.9],
        [-82.4, 34.9],
        [-82.4, 34.8],
        [-82.5, 34.8],
        [-82.5, 34.9]
    ])
    
    # Test case 1: Road entirely inside the area
    road_inside = {
        'coordinates': [
            [
                [-82.45, 34.85],
                [-82.46, 34.86]
            ]
        ]
    }
    
    # Test case 2: Road entirely outside the area
    road_outside = {
        'coordinates': [
            [
                [-82.3, 34.7],
                [-82.2, 34.6]
            ]
        ]
    }
    
    # Test case 3: Road partially inside (some points inside, some outside)
    road_partial = {
        'coordinates': [
            [
                [-82.45, 34.85],  # Inside
                [-82.35, 34.85]   # Outside
            ]
        ]
    }
    
    # Test case 4: Road with multiple segments, one inside
    road_multi_segment = {
        'coordinates': [
            [
                [-82.3, 34.7],    # Outside
                [-82.2, 34.6]     # Outside
            ],
            [
                [-82.45, 34.85],  # Inside
                [-82.46, 34.86]   # Inside
            ]
        ]
    }
    
    all_passed = True
    
    result = check_road_in_area(road_inside, polygon)
    if result:
        print(f"  ✓ Road inside area: correctly detected")
    else:
        print(f"  ✗ Road inside area: not detected")
        all_passed = False
    
    result = check_road_in_area(road_outside, polygon)
    if not result:
        print(f"  ✓ Road outside area: correctly not detected")
    else:
        print(f"  ✗ Road outside area: incorrectly detected")
        all_passed = False
    
    result = check_road_in_area(road_partial, polygon)
    if result:
        print(f"  ✓ Road partially inside area: correctly detected")
    else:
        print(f"  ✗ Road partially inside area: not detected")
        all_passed = False
    
    result = check_road_in_area(road_multi_segment, polygon)
    if result:
        print(f"  ✓ Road with multiple segments (one inside): correctly detected")
    else:
        print(f"  ✗ Road with multiple segments (one inside): not detected")
        all_passed = False
    
    if all_passed:
        print("✓ All check_road_in_area tests passed!")
        return True
    else:
        print("✗ Some check_road_in_area tests failed")
        return False


def test_add_areas_to_roads():
    """Test adding areas to roads"""
    print("\nTesting add_areas_to_roads...")
    
    from shapely.geometry import Polygon
    
    # Create two test areas
    area_a = Polygon([
        [-82.5, 34.9],
        [-82.4, 34.9],
        [-82.4, 34.8],
        [-82.5, 34.8],
        [-82.5, 34.9]
    ])
    
    area_b = Polygon([
        [-82.4, 34.9],
        [-82.3, 34.9],
        [-82.3, 34.8],
        [-82.4, 34.8],
        [-82.4, 34.9]
    ])
    
    areas = {
        'area-a': area_a,
        'area-b': area_b
    }
    
    # Create test roads
    roads = {
        'Road 1': {
            'name': 'Road 1',
            'coordinates': [
                [
                    [-82.45, 34.85],  # In area-a
                    [-82.46, 34.86]   # In area-a
                ]
            ]
        },
        'Road 2': {
            'name': 'Road 2',
            'coordinates': [
                [
                    [-82.35, 34.85],  # In area-b
                    [-82.36, 34.86]   # In area-b
                ]
            ]
        },
        'Road 3': {
            'name': 'Road 3',
            'coordinates': [
                [
                    [-82.45, 34.85],  # In area-a
                    [-82.35, 34.85]   # In area-b
                ]
            ]
        },
        'Road 4': {
            'name': 'Road 4',
            'coordinates': [
                [
                    [-82.2, 34.7],    # Outside both areas
                    [-82.1, 34.6]     # Outside both areas
                ]
            ]
        }
    }
    
    # Add areas to roads
    updated_roads = add_areas_to_roads(roads, areas)
    
    all_passed = True
    
    # Check Road 1 (should be in area-a only)
    if 'area-a' in updated_roads['Road 1']['areas'] and 'area-b' not in updated_roads['Road 1']['areas']:
        print(f"  ✓ Road 1: correctly in area-a only")
    else:
        print(f"  ✗ Road 1: expected area-a, got {updated_roads['Road 1']['areas']}")
        all_passed = False
    
    # Check Road 2 (should be in area-b only)
    if 'area-b' in updated_roads['Road 2']['areas'] and 'area-a' not in updated_roads['Road 2']['areas']:
        print(f"  ✓ Road 2: correctly in area-b only")
    else:
        print(f"  ✗ Road 2: expected area-b, got {updated_roads['Road 2']['areas']}")
        all_passed = False
    
    # Check Road 3 (should be in both areas)
    if 'area-a' in updated_roads['Road 3']['areas'] and 'area-b' in updated_roads['Road 3']['areas']:
        print(f"  ✓ Road 3: correctly in both areas")
    else:
        print(f"  ✗ Road 3: expected both areas, got {updated_roads['Road 3']['areas']}")
        all_passed = False
    
    # Check Road 4 (should be in no areas)
    if len(updated_roads['Road 4']['areas']) == 0:
        print(f"  ✓ Road 4: correctly in no areas")
    else:
        print(f"  ✗ Road 4: expected no areas, got {updated_roads['Road 4']['areas']}")
        all_passed = False
    
    if all_passed:
        print("✓ All add_areas_to_roads tests passed!")
        return True
    else:
        print("✗ Some add_areas_to_roads tests failed")
        return False


def test_areas_field_exists():
    """Test that the areas field exists in roads_formatted.json"""
    print("\nTesting areas field in roads_formatted.json...")
    
    try:
        with open('roads_formatted.json', 'r') as f:
            roads = json.load(f)
        
        if not roads:
            print("  ✗ No roads found in roads_formatted.json")
            return False
        
        # Check that all roads have an areas field
        all_have_areas = True
        for road_name, road_data in roads.items():
            if 'areas' not in road_data:
                print(f"  ✗ Road '{road_name}' missing areas field")
                all_have_areas = False
                break
            
            # Check that areas is a list
            if not isinstance(road_data['areas'], list):
                print(f"  ✗ Road '{road_name}' areas field is not a list")
                all_have_areas = False
                break
        
        if all_have_areas:
            print(f"  ✓ All {len(roads)} roads have areas field as list")
            
            # Show some statistics
            roads_with_areas = sum(1 for road in roads.values() if road['areas'])
            roads_without_areas = len(roads) - roads_with_areas
            
            print(f"  ✓ Roads with at least one area: {roads_with_areas}")
            print(f"  ✓ Roads with no areas: {roads_without_areas}")
            
            # Check for roads with multiple areas
            multi_area_roads = [name for name, data in roads.items() if len(data['areas']) > 1]
            if multi_area_roads:
                print(f"  ✓ Found {len(multi_area_roads)} roads in multiple areas")
                print(f"    Examples: {', '.join(multi_area_roads[:3])}")
            
            return True
        else:
            return False
            
    except FileNotFoundError:
        print("  ✗ roads_formatted.json not found")
        return False
    except Exception as e:
        print(f"  ✗ Error reading roads_formatted.json: {e}")
        return False


if __name__ == '__main__':
    success1 = test_load_area_geojson()
    success2 = test_check_road_in_area()
    success3 = test_add_areas_to_roads()
    success4 = test_areas_field_exists()
    
    sys.exit(0 if (success1 and success2 and success3 and success4) else 1)

