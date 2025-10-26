#!/usr/bin/env python3
"""
Test script for format_roads.py to verify handling of list names
"""
import json
import sys
from format_roads import group_and_combine_roads, extract_road_type

def test_road_type_extraction():
    """Test that road types are extracted correctly from road names"""
    print("Testing road type extraction...")
    
    test_cases = [
        # (road_name, expected_road_type)
        ("Main Street", "Street"),
        ("Oak Avenue", "Avenue"),
        ("Sunset Boulevard", "Boulevard"),
        ("Circle Road", "Road"),  # Should be "Road" not "Circle"
        ("Broadway Parkway", "Parkway"),  # Should be "Parkway" not "Way"
        ("Elm Drive", "Drive"),
        ("Harbor Bay", "Bay"),
        ("Park Court", "Court"),
        ("Willow Cove", "Cove"),
        ("Interstate Expressway", "Expressway"),
        ("Memory Lane", "Lane"),
        ("Market Place", "Place"),
        ("Factory Row", "Row"),
        ("Mountain Spur", "Spur"),
        ("Ocean Way", "Way"),
        ("Circle Circle", "Circle"),  # Edge case: Circle at end
        ("No Road Type Here", None),  # No recognized type
        ("Just A Name", None),  # No recognized type
        ("Avenue", "Avenue"),  # Just the type itself
        ("Street", "Street"),  # Just the type itself
    ]
    
    all_passed = True
    for road_name, expected_type in test_cases:
        actual_type = extract_road_type(road_name)
        if actual_type == expected_type:
            print(f"  ✓ '{road_name}' -> '{actual_type}'")
        else:
            print(f"  ✗ '{road_name}' -> Expected '{expected_type}', got '{actual_type}'")
            all_passed = False
    
    if all_passed:
        print("✓ All road type extraction tests passed!")
        return True
    else:
        print("✗ Some road type extraction tests failed")
        return False


def test_road_type_in_output():
    """Test that road_type field appears in the formatted output"""
    print("\nTesting road_type field in formatted output...")
    
    test_data = [
        {
            'edge_id': '1_2_0',
            'coordinates': [[-122.4194, 37.7749], [-122.4184, 37.7759]],
            'name': 'Main Street'
        },
        {
            'edge_id': '2_3_0',
            'coordinates': [[-122.4184, 37.7759], [-122.4174, 37.7769]],
            'name': 'Circle Road'
        },
        {
            'edge_id': '3_4_0',
            'coordinates': [[-122.4100, 37.7700], [-122.4090, 37.7710]],
            'name': 'Broadway Parkway'
        },
        {
            'edge_id': '4_5_0',
            'coordinates': [[-122.4080, 37.7720], [-122.4070, 37.7730]],
            'name': 'Sunset Boulevard'
        },
    ]
    
    try:
        formatted_roads = group_and_combine_roads(test_data)
        
        # Check that road_type field exists in all roads
        expected_types = {
            'Main Street': 'Street',
            'Circle Road': 'Road',
            'Broadway Parkway': 'Parkway',
            'Sunset Boulevard': 'Boulevard',
        }
        
        all_passed = True
        for road_name, expected_type in expected_types.items():
            if road_name in formatted_roads:
                if 'road_type' in formatted_roads[road_name]:
                    actual_type = formatted_roads[road_name]['road_type']
                    if actual_type == expected_type:
                        print(f"  ✓ '{road_name}' has road_type='{actual_type}'")
                    else:
                        print(f"  ✗ '{road_name}' has road_type='{actual_type}', expected '{expected_type}'")
                        all_passed = False
                else:
                    print(f"  ✗ '{road_name}' missing road_type field")
                    all_passed = False
            else:
                print(f"  ✗ '{road_name}' not found in output")
                all_passed = False
        
        if all_passed:
            print("✓ All roads have correct road_type field!")
            return True
        else:
            print("✗ Some roads have incorrect or missing road_type field")
            return False
            
    except Exception as e:
        print(f"✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_list_names():
    """Test that list names are handled correctly"""
    # Create test data with various name types
    test_data = [
        {
            'edge_id': '1_2_0',
            'coordinates': [[-122.4194, 37.7749], [-122.4184, 37.7759]],
            'name': 'Main Street'
        },
        {
            'edge_id': '2_3_0',
            'coordinates': [[-122.4184, 37.7759], [-122.4174, 37.7769]],
            'name': 'Main Street'
        },
        {
            'edge_id': '3_4_0',
            'coordinates': [[-122.4100, 37.7700], [-122.4090, 37.7710]],
            'name': ['Broadway', 'State Route 47']  # List name with 2 elements
        },
        {
            'edge_id': '4_5_0',
            'coordinates': [[-122.4090, 37.7710], [-122.4080, 37.7720]],
            'name': ['Highway 1']  # List name with 1 element
        },
        {
            'edge_id': '5_6_0',
            'coordinates': [[-122.4080, 37.7720], [-122.4070, 37.7730]],
            'name': ['']  # List with empty string
        },
        {
            'edge_id': '6_7_0',
            'coordinates': [[-122.4070, 37.7730], [-122.4060, 37.7740]],
            'name': []  # Empty list
        }
    ]
    
    print("\nTesting with road segments including various name types...")
    try:
        formatted_roads = group_and_combine_roads(test_data)
        print("✓ Test passed! All name types handled correctly.")
        print(f"  Formatted {len(formatted_roads)} unique roads")
        for road_name in sorted(formatted_roads.keys()):
            segment_count = formatted_roads[road_name]['segment_count']
            print(f"  - '{road_name}' ({segment_count} segment{'s' if segment_count > 1 else ''})")
        
        # Verify expected roads
        expected_roads = {'Main Street', 'Broadway / State Route 47', 'Highway 1'}
        actual_roads = set(formatted_roads.keys())
        
        if expected_roads.issubset(actual_roads):
            print("✓ All expected roads found")
            return True
        else:
            missing = expected_roads - actual_roads
            print(f"✗ Missing expected roads: {missing}")
            return False
            
    except TypeError as e:
        print(f"✗ Test failed with TypeError: {e}")
        return False
    except Exception as e:
        print(f"✗ Test failed with unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_unnamed_roads_filtering():
    """Test that roads named 'unnamed' are filtered out"""
    # Create test data with unnamed roads in various cases
    test_data = [
        {
            'edge_id': '1_2_0',
            'coordinates': [[-122.4194, 37.7749], [-122.4184, 37.7759]],
            'name': 'Main Street'
        },
        {
            'edge_id': '2_3_0',
            'coordinates': [[-122.4184, 37.7759], [-122.4174, 37.7769]],
            'name': 'unnamed'  # lowercase unnamed
        },
        {
            'edge_id': '3_4_0',
            'coordinates': [[-122.4100, 37.7700], [-122.4090, 37.7710]],
            'name': 'Unnamed'  # Capitalized unnamed
        },
        {
            'edge_id': '4_5_0',
            'coordinates': [[-122.4090, 37.7710], [-122.4080, 37.7720]],
            'name': 'UNNAMED'  # All caps unnamed
        },
        {
            'edge_id': '5_6_0',
            'coordinates': [[-122.4080, 37.7720], [-122.4070, 37.7730]],
            'name': 'Oak Street'
        },
        {
            'edge_id': '6_7_0',
            'coordinates': [[-122.4070, 37.7730], [-122.4060, 37.7740]],
            'name': 'UnNaMeD'  # Mixed case unnamed
        }
    ]
    
    print("\nTesting unnamed roads filtering...")
    try:
        formatted_roads = group_and_combine_roads(test_data)
        print("✓ Test passed! Unnamed roads filtered correctly.")
        print(f"  Formatted {len(formatted_roads)} unique roads")
        for road_name in sorted(formatted_roads.keys()):
            segment_count = formatted_roads[road_name]['segment_count']
            print(f"  - '{road_name}' ({segment_count} segment{'s' if segment_count > 1 else ''})")
        
        # Verify only valid named roads are present
        actual_roads = set(formatted_roads.keys())
        expected_roads = {'Main Street', 'Oak Street'}
        
        # Check that unnamed roads are NOT in the output
        unnamed_variations = {'unnamed', 'Unnamed', 'UNNAMED', 'UnNaMeD'}
        found_unnamed = actual_roads.intersection(unnamed_variations)
        
        if found_unnamed:
            print(f"✗ Test failed! Found unnamed roads in output: {found_unnamed}")
            return False
        
        if actual_roads == expected_roads:
            print("✓ All expected roads found and unnamed roads filtered out")
            return True
        else:
            print(f"✗ Unexpected roads found: {actual_roads}")
            print(f"  Expected: {expected_roads}")
            return False
            
    except Exception as e:
        print(f"✗ Test failed with unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success1 = test_road_type_extraction()
    success2 = test_road_type_in_output()
    success3 = test_list_names()
    success4 = test_unnamed_roads_filtering()
    sys.exit(0 if (success1 and success2 and success3 and success4) else 1)
