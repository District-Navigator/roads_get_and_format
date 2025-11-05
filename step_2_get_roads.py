#!/usr/bin/env python3
"""
Get Roads from OpenStreetMap
Downloads all roads within the district boundary from OpenStreetMap using the Overpass API.
Reads the boundary from my_district.geojson and saves road data as JSON.
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.parse
import time


def load_geojson_boundary(geojson_path):
    """
    Load boundary coordinates from a GeoJSON file.
    
    Args:
        geojson_path: Path to the GeoJSON file
        
    Returns:
        dict: The geometry object containing the boundary, or None if not found
    """
    try:
        with open(geojson_path, 'r') as f:
            geojson_data = json.load(f)
        
        # Extract geometry from the first feature
        if 'features' in geojson_data and len(geojson_data['features']) > 0:
            geometry = geojson_data['features'][0].get('geometry')
            if geometry:
                return geometry
    except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
        print(f"Error: Could not load boundary from {geojson_path}: {e}", file=sys.stderr)
    
    return None


def geometry_to_overpass_polygon(geometry):
    """
    Convert a GeoJSON geometry to an Overpass API polygon string.
    
    Args:
        geometry: GeoJSON geometry object (typically a Polygon)
        
    Returns:
        str: Polygon coordinates in Overpass API format (lat lon pairs)
    """
    if geometry.get('type') != 'Polygon':
        raise ValueError(f"Unsupported geometry type: {geometry.get('type')}. Only Polygon is supported.")
    
    # Get the outer ring coordinates (first array in coordinates)
    coordinates = geometry['coordinates'][0]
    
    # Convert to Overpass format: "lat lon lat lon ..."
    # Note: GeoJSON uses [lon, lat] format, Overpass uses "lat lon"
    polygon_parts = []
    for coord in coordinates:
        lon, lat = coord[0], coord[1]
        polygon_parts.append(f"{lat} {lon}")
    
    return " ".join(polygon_parts)


def build_overpass_query(polygon_string):
    """
    Build an Overpass API query to get all roads within a polygon boundary.
    
    Args:
        polygon_string: Polygon coordinates in Overpass format
        
    Returns:
        str: Overpass QL query string
    
    Note:
        The polygon_string is expected to come from a trusted GeoJSON file.
        If using with untrusted input, additional validation should be added.
    """
    # Query for all highway types (roads) within the polygon
    # The query gets ways tagged with highway=* (all road types)
    query = f"""[out:json][timeout:180];
(
  way["highway"](poly:"{polygon_string}");
);
out body;
>;
out skel qt;
"""
    return query


def query_overpass_api(query, overpass_url="https://overpass-api.de/api/interpreter"):
    """
    Send a query to the Overpass API and get the results.
    
    Args:
        query: Overpass QL query string
        overpass_url: URL of the Overpass API endpoint
        
    Returns:
        dict: JSON response from the Overpass API
    """
    print(f"Querying Overpass API at {overpass_url}...", file=sys.stderr)
    print(f"Query length: {len(query)} characters", file=sys.stderr)
    
    try:
        # Encode the query as form data
        data = urllib.parse.urlencode({'data': query}).encode('utf-8')
        
        # Make the request
        req = urllib.request.Request(overpass_url, data=data, method='POST')
        
        print("Sending request to Overpass API (this may take a while)...", file=sys.stderr)
        start_time = time.time()
        
        with urllib.request.urlopen(req, timeout=300) as response:
            elapsed_time = time.time() - start_time
            print(f"Response received in {elapsed_time:.2f} seconds", file=sys.stderr)
            
            result = json.loads(response.read().decode('utf-8'))
            return result
            
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code}: {e.reason}", file=sys.stderr)
        print(f"Response: {e.read().decode('utf-8')}", file=sys.stderr)
        raise
    except urllib.error.URLError as e:
        print(f"URL Error: {e.reason}", file=sys.stderr)
        raise
    except Exception as e:
        print(f"Error querying Overpass API: {e}", file=sys.stderr)
        raise


def save_roads_json(data, output_path):
    """
    Save road data to a JSON file.
    
    Args:
        data: Road data from Overpass API
        output_path: Path to save the JSON file
    """
    try:
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Road data saved to: {output_path}", file=sys.stderr)
    except Exception as e:
        print(f"Error saving road data: {e}", file=sys.stderr)
        raise


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description='Download all roads within the district boundary from OpenStreetMap'
    )
    parser.add_argument(
        '--geojson',
        type=str,
        default='my_district.geojson',
        help='Path to GeoJSON boundary file (default: my_district.geojson)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='roads.json',
        help='Path to output JSON file (default: roads.json)'
    )
    parser.add_argument(
        '--overpass-url',
        type=str,
        default='https://overpass-api.de/api/interpreter',
        help='Overpass API endpoint URL (default: https://overpass-api.de/api/interpreter)'
    )
    
    args = parser.parse_args()
    
    # Resolve geojson path
    geojson_path = args.geojson
    if not os.path.isabs(geojson_path):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        geojson_path = os.path.join(script_dir, geojson_path)
    
    # Resolve output path
    output_path = args.output
    if not os.path.isabs(output_path):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        output_path = os.path.join(script_dir, output_path)
    
    print(f"Loading boundary from: {geojson_path}", file=sys.stderr)
    
    # Load the boundary geometry
    geometry = load_geojson_boundary(geojson_path)
    if not geometry:
        print("Error: Could not load boundary geometry from GeoJSON file", file=sys.stderr)
        return 1
    
    print(f"Boundary type: {geometry.get('type')}", file=sys.stderr)
    
    try:
        # Convert geometry to Overpass polygon format
        polygon_string = geometry_to_overpass_polygon(geometry)
        
        # Build the Overpass query
        query = build_overpass_query(polygon_string)
        
        # Query the Overpass API
        road_data = query_overpass_api(query, args.overpass_url)
        
        # Print some statistics
        elements = road_data.get('elements', [])
        ways = [e for e in elements if e.get('type') == 'way']
        nodes = [e for e in elements if e.get('type') == 'node']
        
        print(f"\nResults:", file=sys.stderr)
        print(f"  Total elements: {len(elements)}", file=sys.stderr)
        print(f"  Roads (ways): {len(ways)}", file=sys.stderr)
        print(f"  Nodes: {len(nodes)}", file=sys.stderr)
        
        # Save the data
        save_roads_json(road_data, output_path)
        
        print(f"\nSuccess! Road data downloaded and saved.", file=sys.stderr)
        return 0
        
    except Exception as e:
        print(f"\nFailed to download road data: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
