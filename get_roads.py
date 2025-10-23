#!/usr/bin/env python3
"""
Program 1: Get Roads from Polygon
Extracts all road data from OpenStreetMap within a polygon defined in my_district.geojson
Outputs the raw road data to roads_raw.json
"""

import json
import geopandas as gpd
import osmnx as ox
from shapely.geometry import shape
from format_roads import normalize_road_name


def load_district_polygon(geojson_file):
    """
    Load the district polygon from a GeoJSON file.
    
    Args:
        geojson_file: Path to the GeoJSON file containing the district polygon
        
    Returns:
        shapely.geometry.Polygon: The district boundary polygon
    """
    with open(geojson_file, 'r') as f:
        geojson_data = json.load(f)
    
    # Extract the first feature's geometry
    if geojson_data['type'] == 'FeatureCollection':
        geometry = geojson_data['features'][0]['geometry']
    else:
        geometry = geojson_data['geometry']
    
    polygon = shape(geometry)
    return polygon


def get_roads_from_polygon(polygon):
    """
    Fetch all roads within the given polygon from OpenStreetMap.
    
    Args:
        polygon: shapely.geometry.Polygon defining the area
        
    Returns:
        networkx.MultiDiGraph: Road network graph
    """
    # Get the street network within the polygon
    # Using 'drive' network type to get all drivable roads
    G = ox.graph_from_polygon(polygon, network_type='drive')
    return G


def extract_road_data(G):
    """
    Extract road segment data from the OSMnx graph.
    
    Args:
        G: networkx.MultiDiGraph from OSMnx
        
    Returns:
        list: List of dictionaries containing road segment information
    """
    roads_data = []
    
    for u, v, key, data in G.edges(keys=True, data=True):
        # Get node coordinates
        u_node = G.nodes[u]
        v_node = G.nodes[v]
        
        # Extract geometry if available, otherwise use straight line
        if 'geometry' in data:
            coords = list(data['geometry'].coords)
        else:
            coords = [(u_node['x'], u_node['y']), (v_node['x'], v_node['y'])]
        
        # Get road name and normalize if it's a list
        road_name = normalize_road_name(data.get('name', 'Unknown'))
        
        # Build road segment dictionary
        road_segment = {
            'edge_id': f"{u}_{v}_{key}",
            'start_node': u,
            'end_node': v,
            'coordinates': coords,
            'name': road_name,
            'highway': data.get('highway', 'unknown'),
            'length': data.get('length', 0),
            'oneway': data.get('oneway', False),
            'osmid': data.get('osmid', None)
        }
        
        roads_data.append(road_segment)
    
    return roads_data


def save_roads_data(roads_data, output_file):
    """
    Save the roads data to a JSON file.
    
    Args:
        roads_data: List of road segment dictionaries
        output_file: Path to output JSON file
    """
    with open(output_file, 'w') as f:
        json.dump(roads_data, f, indent=2)
    
    print(f"Saved {len(roads_data)} road segments to {output_file}")


def main():
    """Main execution function."""
    input_geojson = 'my_district.geojson'
    output_json = 'roads_raw.json'
    
    print(f"Loading district polygon from {input_geojson}...")
    polygon = load_district_polygon(input_geojson)
    
    print("Fetching roads from OpenStreetMap...")
    G = get_roads_from_polygon(polygon)
    
    print(f"Extracting data from {len(G.edges)} road segments...")
    roads_data = extract_road_data(G)
    
    print(f"Saving roads data to {output_json}...")
    save_roads_data(roads_data, output_json)
    
    print("Done!")


if __name__ == '__main__':
    main()
