#!/usr/bin/env python3
"""
Test script for format_roads.py to verify handling of list names
"""
import json
import sys
from format_roads import group_and_combine_roads

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
    
    print("Testing with road segments including various name types...")
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

if __name__ == '__main__':
    success = test_list_names()
    sys.exit(0 if success else 1)
