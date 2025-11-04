#!/usr/bin/env python3
"""
Example: Using the Unified District Creation Program

This script demonstrates different ways to use create_district_complete.py
to create a complete district with roads, areas, and sub-areas.
"""

import subprocess
import sys

def print_section(title):
    """Print a formatted section header."""
    print("\n" + "="*70)
    print(title)
    print("="*70 + "\n")


def example_1_interactive():
    """
    Example 1: Interactive mode
    The program will prompt for all required inputs.
    """
    print_section("Example 1: Interactive Mode")
    
    print("To use interactive mode, simply run:")
    print("  python create_district_complete.py my_district.geojson")
    print()
    print("The program will prompt you for:")
    print("  - District name")
    print("  - District key (auto-generated suggestion provided)")
    print("  - District status")
    print("  - Creator user ID")
    print("  - Whether to fetch fresh data from OpenStreetMap")
    print()
    print("This is the easiest way to get started!")


def example_2_non_interactive():
    """
    Example 2: Non-interactive mode with command-line arguments
    All inputs provided via CLI flags - no prompts.
    """
    print_section("Example 2: Non-Interactive Mode (Full Automation)")
    
    print("For automation or scripting, use command-line arguments:")
    print()
    print("  python create_district_complete.py my_district.geojson \\")
    print("    --name 'North Hills District' \\")
    print("    --key north-hills \\")
    print("    --status active \\")
    print("    --creator-id 42 \\")
    print("    --output north_hills_upload.json")
    print()
    print("This mode is perfect for:")
    print("  - Automated scripts")
    print("  - CI/CD pipelines")
    print("  - Batch processing multiple districts")


def example_3_custom_folders():
    """
    Example 3: Using custom areas and sub-areas folders
    """
    print_section("Example 3: Custom Areas and Sub-Areas Folders")
    
    print("If your areas are in different folders, specify them:")
    print()
    print("  python create_district_complete.py my_district.geojson \\")
    print("    --name 'My District' \\")
    print("    --key my-district \\")
    print("    --areas-folder custom_areas \\")
    print("    --sub-areas-folder custom_sub_areas")
    print()
    print("The program will:")
    print("  1. Load area GeoJSON files from custom_areas/")
    print("  2. Load sub-area GeoJSON files from custom_sub_areas/")
    print("  3. Automatically assign roads to areas based on coordinates")


def example_4_fetch_fresh_data():
    """
    Example 4: Fetching fresh data from OpenStreetMap
    """
    print_section("Example 4: Fetch Fresh Data from OpenStreetMap")
    
    print("To fetch fresh road data from OSM (instead of using cached data):")
    print()
    print("  python create_district_complete.py my_district.geojson \\")
    print("    --name 'My District' \\")
    print("    --key my-district \\")
    print("    --online")
    print()
    print("Note: This requires internet access and may take several minutes")
    print("      depending on the size of your district.")
    print()
    print("By default, the program uses cached data from roads_raw.json if available.")


def example_5_minimal():
    """
    Example 5: Minimal district (no creator, no areas)
    """
    print_section("Example 5: Minimal District Creation")
    
    print("To create a minimal district without creator or areas:")
    print()
    print("  python create_district_complete.py my_district.geojson \\")
    print("    --name 'Simple District' \\")
    print("    --key simple-district \\")
    print("    --areas-folder /tmp/empty \\")
    print("    --sub-areas-folder /tmp/empty")
    print()
    print("This creates a district with:")
    print("  - District border")
    print("  - Roads (without area assignments)")
    print("  - No district members")


def example_6_workflow():
    """
    Example 6: Complete workflow from start to finish
    """
    print_section("Example 6: Complete Workflow")
    
    print("Here's a complete workflow for creating a new district:")
    print()
    print("1. Prepare your district border GeoJSON file:")
    print("   - Draw the border on a map tool (e.g., geojson.io)")
    print("   - Save as 'my_district.geojson'")
    print()
    print("2. (Optional) Create area GeoJSON files:")
    print("   - Create 'areas/' folder")
    print("   - Add GeoJSON files for each area (e.g., 'station-8.geojson')")
    print()
    print("3. (Optional) Create sub-area GeoJSON files:")
    print("   - Create 'sub_areas/' folder")
    print("   - Add GeoJSON files for each sub-area")
    print()
    print("4. Run the unified program:")
    print("   python create_district_complete.py my_district.geojson \\")
    print("     --name 'My District' \\")
    print("     --key my-district \\")
    print("     --creator-id 42")
    print()
    print("5. Upload the generated JSON file to your API:")
    print("   curl -X POST https://api.example.com/districts \\")
    print("     -H 'Content-Type: application/json' \\")
    print("     -d @district_upload_complete.json")


def main():
    """Run all examples."""
    print("="*70)
    print("UNIFIED DISTRICT CREATION - USAGE EXAMPLES")
    print("="*70)
    print()
    print("This guide shows different ways to use create_district_complete.py")
    print("to create a complete district with roads, areas, and sub-areas.")
    
    example_1_interactive()
    example_2_non_interactive()
    example_3_custom_folders()
    example_4_fetch_fresh_data()
    example_5_minimal()
    example_6_workflow()
    
    print()
    print("="*70)
    print("For more information, run:")
    print("  python create_district_complete.py --help")
    print("="*70)
    print()


if __name__ == '__main__':
    main()
