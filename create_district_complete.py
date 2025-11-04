#!/usr/bin/env python3
"""
Complete District Creation Program
Condenses the entire district creation workflow into a single program.

This program takes a district border GeoJSON, areas folder, sub-areas folder,
and user inputs to create a complete district upload payload including:
- District object with border coordinates
- Roads extracted from OpenStreetMap
- Area and sub-area assignments for roads
- Comprehensive upload payload ready for API submission
"""

import json
import sys
import os
import argparse
from pathlib import Path

# Import functions from existing modules
from get_roads import (
    load_district_polygon,
    get_roads_from_polygon,
    extract_road_data,
    group_and_combine_roads,
    save_roads_data
)
from add_areas import (
    load_all_areas,
    add_areas_to_roads
)
from create_district import (
    create_district_from_geojson,
    slugify,
    validate_district_key,
    validate_district_name
)
from create_district_upload import (
    create_area_object,
    create_road_object,
    create_district_member_object,
    create_comprehensive_upload,
    save_upload_payload
)


def prompt_user_input(prompt_text, default=None, input_type=str, validator=None):
    """
    Prompt user for input with optional default value and validation.
    
    Args:
        prompt_text: Text to display to user
        default: Default value if user presses enter
        input_type: Type to convert input to (str, int, etc.)
        validator: Optional validation function that raises ValueError if invalid
        
    Returns:
        User input converted to input_type
    """
    while True:
        if default is not None:
            user_input = input(f"{prompt_text} [{default}]: ").strip()
            if not user_input:
                user_input = default
        else:
            user_input = input(f"{prompt_text}: ").strip()
            if not user_input:
                print("This field is required. Please enter a value.")
                continue
        
        try:
            # Convert to appropriate type
            if input_type == int:
                value = int(user_input)
            elif input_type == bool:
                value = user_input.lower() in ['yes', 'y', 'true', '1']
            else:
                value = str(user_input)
            
            # Validate if validator provided
            if validator:
                validator(value)
            
            return value
        except ValueError as e:
            print(f"Invalid input: {e}")
            print("Please try again.")


def get_user_inputs(district_geojson_file):
    """
    Prompt user for all required district information.
    
    Args:
        district_geojson_file: Path to district border GeoJSON file
        
    Returns:
        dict: Dictionary containing all user inputs
    """
    print("\n" + "="*70)
    print("DISTRICT CREATION - User Input")
    print("="*70)
    
    # Auto-generate default name from filename
    file_stem = Path(district_geojson_file).stem
    default_name = file_stem.replace('_', ' ').replace('-', ' ').title()
    
    # Get district name
    print("\n1. District Name")
    print("   (Human-readable name for the district)")
    district_name = prompt_user_input(
        "Enter district name",
        default=default_name,
        validator=validate_district_name
    )
    
    # Get district key (slug)
    print("\n2. District Key")
    print("   (Unique URL-safe identifier, lowercase with hyphens)")
    default_key = slugify(district_name)
    district_key = prompt_user_input(
        "Enter district key",
        default=default_key,
        validator=validate_district_key
    )
    
    # Get district status
    print("\n3. District Status")
    print("   (Status of the district: active, archived, or disabled)")
    district_status = prompt_user_input(
        "Enter district status",
        default="active"
    )
    if district_status not in ['active', 'archived', 'disabled']:
        print(f"Warning: '{district_status}' is not a standard status. Using anyway.")
    
    # Get creator/owner ID
    print("\n4. Creator/Owner User ID")
    print("   (User ID of the person creating this district)")
    print("   (Leave blank to skip)")
    creator_input = input("Enter creator user ID [skip]: ").strip()
    creator_id = int(creator_input) if creator_input else None
    
    # Get whether to fetch fresh data from OSM
    print("\n5. OpenStreetMap Data")
    print("   (Fetch fresh road data from OpenStreetMap or use existing data)")
    use_online = prompt_user_input(
        "Fetch fresh data from OSM? (yes/no)",
        default="no",
        input_type=bool
    )
    
    return {
        'name': district_name,
        'key': district_key,
        'status': district_status,
        'creator_id': creator_id,
        'use_online': use_online
    }


def load_or_fetch_roads(district_polygon, use_online=False, roads_raw_file='roads_raw.json'):
    """
    Load roads from existing file or fetch from OpenStreetMap.
    
    Args:
        district_polygon: Shapely polygon defining the district
        use_online: If True, fetch fresh data from OSM
        roads_raw_file: Path to raw roads JSON file
        
    Returns:
        list: Raw roads data (list of road segments)
    """
    if use_online or not os.path.exists(roads_raw_file):
        print("\nFetching road data from OpenStreetMap...")
        print("(This may take a few minutes depending on the area size)")
        
        try:
            # Fetch roads from OSM
            graph = get_roads_from_polygon(district_polygon)
            
            # Extract segments from graph
            roads_raw = extract_road_data(graph)
            
            # Save raw data for future use
            save_roads_data(roads_raw, roads_raw_file)
            print(f"Saved raw road data to {roads_raw_file}")
            
            return roads_raw
        except Exception as e:
            print(f"Error fetching roads from OpenStreetMap: {e}")
            print("Tip: Check your internet connection and try again.")
            sys.exit(1)
    else:
        print(f"\nLoading road data from {roads_raw_file}...")
        with open(roads_raw_file, 'r') as f:
            roads_raw = json.load(f)
        print(f"Loaded {len(roads_raw)} road segments")
        return roads_raw


def convert_formatted_roads_to_road_objects(formatted_roads, district_key):
    """
    Convert formatted roads dictionary to road objects for upload.
    
    Args:
        formatted_roads: Dictionary of formatted road data
        district_key: District key to use as prefix for road keys
        
    Returns:
        list: List of road objects ready for upload
    """
    road_objects = []
    
    for idx, (road_name, road_data) in enumerate(formatted_roads.items(), start=1):
        # Generate unique key for road
        road_key_base = slugify(road_name)
        road_key = f"{district_key}-{road_key_base}"
        
        # Map size 'big' to 'large' for compatibility with upload schema
        size = road_data.get('size')
        if size == 'big':
            size = 'large'
        
        # Create road object
        road_obj = create_road_object(
            temp_id=f"road-{idx}",
            key=road_key[:255],  # Ensure key doesn't exceed max length
            name=road_name[:255],  # Ensure name doesn't exceed max length
            road_type=road_data.get('road_type'),
            length=road_data.get('length'),
            size=size,
            segments=None,  # We can add detailed segments if needed
            areas=road_data.get('areas', []),
            coordinates=road_data.get('coordinates'),
            sub_areas=1 if len(road_data.get('sub_areas', [])) > 0 else 0
        )
        
        road_objects.append(road_obj)
    
    return road_objects


def convert_areas_to_area_objects(areas_dict, is_sub_area=False, creator_id=None):
    """
    Convert area polygons to area objects for upload.
    
    Args:
        areas_dict: Dictionary mapping area names to Shapely polygons
        is_sub_area: True if these are sub-areas
        creator_id: Creator user ID
        
    Returns:
        list: List of area objects ready for upload
    """
    area_objects = []
    
    for idx, (area_name, polygon) in enumerate(areas_dict.items(), start=1):
        # Convert Shapely polygon to GeoJSON
        geojson_coords = list(polygon.exterior.coords)
        area_border_coordinates = {
            "type": "Polygon",
            "coordinates": [geojson_coords]
        }
        
        # Create area object
        area_obj = create_area_object(
            temp_id=f"{'subarea' if is_sub_area else 'area'}-{idx}",
            name=area_name,
            area_border_coordinates=area_border_coordinates,
            status='active',
            sub_area=1 if is_sub_area else 0,
            created_by=creator_id
        )
        
        area_objects.append(area_obj)
    
    return area_objects


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description='Create a complete district with roads, areas, and sub-areas.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode (will prompt for all inputs)
  python create_district_complete.py my_district.geojson

  # Non-interactive mode with all parameters
  python create_district_complete.py my_district.geojson \\
    --name "North Hills" --key north-hills \\
    --creator-id 42 --online

  # Using custom areas and sub-areas folders
  python create_district_complete.py my_district.geojson \\
    --areas-folder custom_areas --sub-areas-folder custom_sub_areas
        """
    )
    
    parser.add_argument(
        'district_geojson',
        help='Path to district border GeoJSON file'
    )
    parser.add_argument(
        '--areas-folder',
        default='areas',
        help='Path to folder containing area GeoJSON files (default: areas)'
    )
    parser.add_argument(
        '--sub-areas-folder',
        default='sub_areas',
        help='Path to folder containing sub-area GeoJSON files (default: sub_areas)'
    )
    parser.add_argument(
        '--output',
        default='district_upload_complete.json',
        help='Output file for the complete district upload payload (default: district_upload_complete.json)'
    )
    
    # Optional non-interactive parameters
    parser.add_argument('--name', help='District name (will prompt if not provided)')
    parser.add_argument('--key', help='District key/slug (will auto-generate if not provided)')
    parser.add_argument('--status', default='active', help='District status (default: active)')
    parser.add_argument('--creator-id', type=int, help='Creator user ID')
    parser.add_argument('--online', action='store_true', help='Fetch fresh data from OpenStreetMap')
    parser.add_argument('--roads-raw', default='roads_raw.json', help='Path to raw roads JSON file')
    
    args = parser.parse_args()
    
    # Verify district GeoJSON file exists
    if not os.path.exists(args.district_geojson):
        print(f"Error: District GeoJSON file not found: {args.district_geojson}")
        sys.exit(1)
    
    print("="*70)
    print("COMPLETE DISTRICT CREATION PROGRAM")
    print("="*70)
    print(f"\nDistrict border: {args.district_geojson}")
    print(f"Areas folder: {args.areas_folder}")
    print(f"Sub-areas folder: {args.sub_areas_folder}")
    print(f"Output file: {args.output}")
    
    # Get user inputs (interactive or from command-line args)
    if args.name and args.key:
        # Non-interactive mode
        user_inputs = {
            'name': args.name,
            'key': args.key,
            'status': args.status,
            'creator_id': args.creator_id,
            'use_online': args.online
        }
        print("\nUsing command-line parameters:")
        print(f"  Name: {user_inputs['name']}")
        print(f"  Key: {user_inputs['key']}")
        print(f"  Status: {user_inputs['status']}")
        print(f"  Creator ID: {user_inputs['creator_id']}")
        print(f"  Fetch from OSM: {user_inputs['use_online']}")
    else:
        # Interactive mode
        user_inputs = get_user_inputs(args.district_geojson)
    
    # Step 1: Create district object
    print("\n" + "="*70)
    print("STEP 1: Creating District Object")
    print("="*70)
    
    district = create_district_from_geojson(
        args.district_geojson,
        key=user_inputs['key'],
        name=user_inputs['name'],
        status=user_inputs['status'],
        road_count=0,  # Will be updated after processing roads
        owner=user_inputs['creator_id'],
        created_by=user_inputs['creator_id']
    )
    print(f"✓ Created district: {district['name']} (key: {district['key']})")
    
    # Step 2: Load or fetch roads
    print("\n" + "="*70)
    print("STEP 2: Loading/Fetching Road Data")
    print("="*70)
    
    district_polygon = load_district_polygon(args.district_geojson)
    roads_raw = load_or_fetch_roads(
        district_polygon,
        use_online=user_inputs['use_online'],
        roads_raw_file=args.roads_raw
    )
    
    # Step 3: Format roads
    print("\n" + "="*70)
    print("STEP 3: Formatting Roads")
    print("="*70)
    
    formatted_roads = group_and_combine_roads(roads_raw, district_id=None)
    print(f"✓ Formatted {len(formatted_roads)} roads")
    
    # Step 4: Load areas and sub-areas
    print("\n" + "="*70)
    print("STEP 4: Loading Areas and Sub-Areas")
    print("="*70)
    
    areas = load_all_areas(args.areas_folder)
    sub_areas = load_all_areas(args.sub_areas_folder)
    
    # Step 5: Add area/sub-area assignments to roads
    print("\n" + "="*70)
    print("STEP 5: Assigning Areas/Sub-Areas to Roads")
    print("="*70)
    
    if areas or sub_areas:
        formatted_roads = add_areas_to_roads(formatted_roads, areas, sub_areas)
        print("✓ Area/sub-area assignments complete")
    else:
        print("No areas or sub-areas found. Skipping area assignments.")
        # Initialize empty area lists for all roads
        for road_data in formatted_roads.values():
            road_data['areas'] = []
            road_data['sub_areas'] = []
    
    # Step 6: Convert to upload objects
    print("\n" + "="*70)
    print("STEP 6: Creating Upload Payload")
    print("="*70)
    
    # Convert areas to area objects
    area_objects = []
    if areas:
        area_objects.extend(
            convert_areas_to_area_objects(areas, is_sub_area=False, creator_id=user_inputs['creator_id'])
        )
    if sub_areas:
        area_objects.extend(
            convert_areas_to_area_objects(sub_areas, is_sub_area=True, creator_id=user_inputs['creator_id'])
        )
    
    print(f"✓ Created {len(area_objects)} area objects")
    
    # Convert roads to road objects
    road_objects = convert_formatted_roads_to_road_objects(formatted_roads, user_inputs['key'])
    print(f"✓ Created {len(road_objects)} road objects")
    
    # Update district road count
    district['road_count'] = len(road_objects)
    
    # Create district members if creator_id provided
    district_members = []
    if user_inputs['creator_id']:
        district_members.append(
            create_district_member_object(
                user_id=user_inputs['creator_id'],
                role='admin',
                permissions=['manage_roads', 'manage_areas', 'manage_members']
            )
        )
        print(f"✓ Added creator as district admin")
    
    # Create comprehensive upload payload
    upload = create_comprehensive_upload(
        district=district,
        areas=area_objects if area_objects else None,
        roads=road_objects if road_objects else None,
        district_members=district_members if district_members else None
    )
    
    # Step 7: Save output
    print("\n" + "="*70)
    print("STEP 7: Saving Output")
    print("="*70)
    
    save_upload_payload(upload, args.output)
    
    # Print summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"District: {district['name']} (key: {district['key']})")
    print(f"Status: {district['status']}")
    print(f"Roads: {len(road_objects)}")
    print(f"Areas: {len([a for a in area_objects if a['sub_area'] == 0])} areas")
    print(f"Sub-areas: {len([a for a in area_objects if a['sub_area'] == 1])} sub-areas")
    print(f"Members: {len(district_members)}")
    print(f"\nOutput saved to: {args.output}")
    print("\n✓ District creation complete!")
    print("\nYou can now upload this file to your API endpoint.")


if __name__ == '__main__':
    main()
