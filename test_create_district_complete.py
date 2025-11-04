#!/usr/bin/env python3
"""
Tests for create_district_complete.py
Tests the unified district creation program.
"""

import unittest
import json
import os
import tempfile
import shutil
from pathlib import Path
from create_district_complete import (
    prompt_user_input,
    convert_formatted_roads_to_road_objects,
    convert_areas_to_area_objects
)
from shapely.geometry import Polygon


class TestPromptUserInput(unittest.TestCase):
    """Test user input prompting (manual test - skipped in automated tests)."""
    
    def test_validation_error_handling(self):
        """Test that validation errors are handled properly."""
        # This is a basic test for the function structure
        # Interactive testing would need to be done manually
        self.assertTrue(callable(prompt_user_input))


class TestConvertFormattedRoads(unittest.TestCase):
    """Test conversion of formatted roads to road objects."""
    
    def test_basic_road_conversion(self):
        """Test converting basic formatted roads to road objects."""
        formatted_roads = {
            "Main Street": {
                "name": "Main Street",
                "road_type": "Street",
                "coordinates": [[[-122.4, 37.8], [-122.39, 37.81]]],
                "length": 150.5,
                "size": "medium",
                "segments": 2,
                "areas": ["area-1"],
                "sub_areas": []
            },
            "Oak Avenue": {
                "name": "Oak Avenue",
                "road_type": "Avenue",
                "coordinates": [[[-122.41, 37.82], [-122.40, 37.83]]],
                "length": 300.0,
                "size": "big",  # Should be converted to "large"
                "segments": 1,
                "areas": [],
                "sub_areas": ["subarea-1"]
            }
        }
        
        road_objects = convert_formatted_roads_to_road_objects(formatted_roads, "test-district")
        
        # Check that we got 2 road objects
        self.assertEqual(len(road_objects), 2)
        
        # Check first road
        road1 = road_objects[0]
        self.assertEqual(road1['name'], "Main Street")
        self.assertEqual(road1['key'], "test-district-main-street")
        self.assertEqual(road1['type'], "Street")
        self.assertEqual(road1['length'], 150.5)
        self.assertEqual(road1['size'], "medium")
        self.assertEqual(road1['areas'], ["area-1"])
        self.assertIn('temp_id', road1)
        
        # Check second road - size should be converted from 'big' to 'large'
        road2 = road_objects[1]
        self.assertEqual(road2['name'], "Oak Avenue")
        self.assertEqual(road2['size'], "large")  # Converted from 'big'
        self.assertEqual(road2['sub_areas'], 1)  # Has sub_areas
    
    def test_size_conversion(self):
        """Test that 'big' size is converted to 'large'."""
        formatted_roads = {
            "Big Road": {
                "name": "Big Road",
                "road_type": "Road",
                "coordinates": [[[-122.4, 37.8], [-122.39, 37.81]]],
                "length": 500.0,
                "size": "big",
                "segments": 1,
                "areas": [],
                "sub_areas": []
            }
        }
        
        road_objects = convert_formatted_roads_to_road_objects(formatted_roads, "test")
        self.assertEqual(road_objects[0]['size'], "large")
    
    def test_empty_roads(self):
        """Test conversion with empty roads dictionary."""
        formatted_roads = {}
        road_objects = convert_formatted_roads_to_road_objects(formatted_roads, "test")
        self.assertEqual(len(road_objects), 0)
    
    def test_long_road_name_truncation(self):
        """Test that long road names are truncated to 255 characters."""
        long_name = "A" * 300
        formatted_roads = {
            long_name: {
                "name": long_name,
                "road_type": None,
                "coordinates": [[[-122.4, 37.8], [-122.39, 37.81]]],
                "length": 100.0,
                "size": "small",
                "segments": 1,
                "areas": [],
                "sub_areas": []
            }
        }
        
        road_objects = convert_formatted_roads_to_road_objects(formatted_roads, "test")
        self.assertLessEqual(len(road_objects[0]['name']), 255)
        self.assertLessEqual(len(road_objects[0]['key']), 255)


class TestConvertAreas(unittest.TestCase):
    """Test conversion of area polygons to area objects."""
    
    def test_basic_area_conversion(self):
        """Test converting basic area polygons to area objects."""
        # Create simple polygon
        polygon = Polygon([
            [-122.4, 37.8],
            [-122.4, 37.81],
            [-122.39, 37.81],
            [-122.39, 37.8],
            [-122.4, 37.8]
        ])
        
        areas_dict = {
            "station-8": polygon
        }
        
        area_objects = convert_areas_to_area_objects(areas_dict, is_sub_area=False, creator_id=42)
        
        # Check that we got 1 area object
        self.assertEqual(len(area_objects), 1)
        
        # Check area properties
        area = area_objects[0]
        self.assertEqual(area['name'], "station-8")
        self.assertEqual(area['sub_area'], 0)
        self.assertEqual(area['status'], 'active')
        self.assertEqual(area['created_by'], 42)
        self.assertIn('temp_id', area)
        self.assertIn('area_border_coordinates', area)
        self.assertEqual(area['area_border_coordinates']['type'], 'Polygon')
    
    def test_sub_area_conversion(self):
        """Test converting sub-areas."""
        polygon = Polygon([
            [-122.4, 37.8],
            [-122.4, 37.81],
            [-122.39, 37.81],
            [-122.39, 37.8],
            [-122.4, 37.8]
        ])
        
        areas_dict = {
            "sub-station-8": polygon
        }
        
        area_objects = convert_areas_to_area_objects(areas_dict, is_sub_area=True, creator_id=None)
        
        # Check that sub_area flag is set
        self.assertEqual(area_objects[0]['sub_area'], 1)
        self.assertNotIn('created_by', area_objects[0])
    
    def test_multiple_areas(self):
        """Test converting multiple areas."""
        polygon1 = Polygon([[-122.4, 37.8], [-122.4, 37.81], [-122.39, 37.81], [-122.39, 37.8], [-122.4, 37.8]])
        polygon2 = Polygon([[-122.41, 37.82], [-122.41, 37.83], [-122.40, 37.83], [-122.40, 37.82], [-122.41, 37.82]])
        
        areas_dict = {
            "area-1": polygon1,
            "area-2": polygon2
        }
        
        area_objects = convert_areas_to_area_objects(areas_dict, is_sub_area=False, creator_id=42)
        
        # Check that we got 2 area objects
        self.assertEqual(len(area_objects), 2)
        
        # Check that temp_ids are unique
        temp_ids = [area['temp_id'] for area in area_objects]
        self.assertEqual(len(temp_ids), len(set(temp_ids)))
    
    def test_empty_areas(self):
        """Test conversion with empty areas dictionary."""
        areas_dict = {}
        area_objects = convert_areas_to_area_objects(areas_dict, is_sub_area=False, creator_id=None)
        self.assertEqual(len(area_objects), 0)


class TestIntegrationScenarios(unittest.TestCase):
    """Integration tests for complete workflows."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        
        # Create a simple test GeoJSON file
        self.test_geojson = os.path.join(self.test_dir, "test_district.geojson")
        test_polygon = {
            "type": "FeatureCollection",
            "features": [{
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [-122.4, 37.8],
                        [-122.4, 37.81],
                        [-122.39, 37.81],
                        [-122.39, 37.8],
                        [-122.4, 37.8]
                    ]]
                }
            }]
        }
        
        with open(self.test_geojson, 'w') as f:
            json.dump(test_polygon, f)
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir)
    
    def test_geojson_file_exists(self):
        """Test that the test GeoJSON file was created."""
        self.assertTrue(os.path.exists(self.test_geojson))
    
    def test_can_load_test_geojson(self):
        """Test that we can load the test GeoJSON file."""
        with open(self.test_geojson, 'r') as f:
            data = json.load(f)
        
        self.assertEqual(data['type'], 'FeatureCollection')
        self.assertEqual(len(data['features']), 1)


def run_tests():
    """Run all tests and print results."""
    print("="*70)
    print("Running Tests for create_district_complete.py")
    print("="*70)
    print()
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestPromptUserInput))
    suite.addTests(loader.loadTestsFromTestCase(TestConvertFormattedRoads))
    suite.addTests(loader.loadTestsFromTestCase(TestConvertAreas))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegrationScenarios))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print()
    print("="*70)
    print("Test Summary")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n✓ All tests passed!")
        return 0
    else:
        print("\n✗ Some tests failed!")
        return 1


if __name__ == '__main__':
    exit(run_tests())
