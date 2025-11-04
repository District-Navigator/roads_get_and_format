#!/usr/bin/env python3
"""
Comprehensive District Upload Creator
Creates a complete district upload payload including district, areas, roads, 
members, attachments, and events. Supports nested creation with temporary ID references.
"""

import json
from pathlib import Path
from create_district import slugify, validate_geojson_polygon


def create_area_object(
    temp_id,
    name,
    area_border_coordinates=None,
    status='active',
    sub_area=0,
    created_by=None
):
    """
    Create an area object for nested district upload.
    
    Args:
        temp_id: Client-side temporary ID for reference (string)
        name: Human-readable area name (required)
        area_border_coordinates: GeoJSON Polygon or MultiPolygon object
        status: Area status ('active', 'archived', 'disabled')
        sub_area: 0 for regular area, 1 for sub-area
        created_by: Creator user ID (integer or None)
        
    Returns:
        dict: Area object for upload payload
    """
    if not name:
        raise ValueError("Area name cannot be empty")
    
    if sub_area not in [0, 1]:
        raise ValueError("sub_area must be 0 or 1")
    
    area = {
        "temp_id": temp_id,
        "name": name,
        "status": status,
        "sub_area": sub_area
    }
    
    if area_border_coordinates is not None:
        validate_geojson_polygon(area_border_coordinates)
        area["area_border_coordinates"] = area_border_coordinates
    
    if created_by is not None:
        if not isinstance(created_by, int):
            raise ValueError("created_by must be an integer (user ID)")
        area["created_by"] = created_by
    
    return area


def create_road_object(
    temp_id,
    key,
    name,
    road_type=None,
    length=None,
    size=None,
    segments=None,
    areas=None,
    coordinates=None,
    sub_areas=0
):
    """
    Create a road object for nested district upload.
    
    Args:
        temp_id: Client-side temporary ID for reference (string)
        key: Unique road slug (required)
        name: Human-readable road name (required)
        road_type: Road type (e.g., 'primary', 'secondary', 'residential')
        length: Length in meters (number)
        size: Size category ('small', 'medium', 'large')
        segments: Array of segment objects with id, from, to, length_m
        areas: Array of area temp_ids this road intersects
        coordinates: GeoJSON LineString object or array of [lng, lat] pairs
        sub_areas: 0 or 1
        
    Returns:
        dict: Road object for upload payload
    """
    if not key:
        raise ValueError("Road key cannot be empty")
    
    if not name:
        raise ValueError("Road name cannot be empty")
    
    # Validate key format (slug)
    if not key.islower():
        raise ValueError("Road key must be lowercase")
    
    road = {
        "temp_id": temp_id,
        "key": key,
        "name": name
    }
    
    if road_type is not None:
        road["type"] = road_type
    
    if length is not None:
        if not isinstance(length, (int, float)) or length < 0:
            raise ValueError("Road length must be a non-negative number")
        road["length"] = length
    
    if size is not None:
        if size not in ['small', 'medium', 'large']:
            raise ValueError("Road size must be 'small', 'medium', or 'large'")
        road["size"] = size
    
    if segments is not None:
        if not isinstance(segments, list):
            raise ValueError("Road segments must be a list")
        road["segments"] = segments
    
    if areas is not None:
        if not isinstance(areas, list):
            raise ValueError("Road areas must be a list")
        road["areas"] = areas
    
    if coordinates is not None:
        # Validate coordinates (should be GeoJSON LineString or array)
        if isinstance(coordinates, dict):
            if coordinates.get('type') != 'LineString':
                raise ValueError("Coordinates GeoJSON must be type 'LineString'")
            if 'coordinates' not in coordinates:
                raise ValueError("GeoJSON LineString must have 'coordinates' field")
        road["coordinates"] = coordinates
    
    if sub_areas not in [0, 1]:
        raise ValueError("sub_areas must be 0 or 1")
    road["sub_areas"] = sub_areas
    
    return road


def create_district_member_object(user_id, role='member', permissions=None, active=1):
    """
    Create a district member object.
    
    Args:
        user_id: User ID (integer, required)
        role: Member role ('member', 'admin', 'editor', 'viewer')
        permissions: List of permission strings
        active: 1 for active, 0 for inactive
        
    Returns:
        dict: District member object
    """
    if not isinstance(user_id, int):
        raise ValueError("user_id must be an integer")
    
    if active not in [0, 1]:
        raise ValueError("active must be 0 or 1")
    
    member = {
        "user_id": user_id,
        "role": role,
        "active": active
    }
    
    if permissions is not None:
        if not isinstance(permissions, list):
            raise ValueError("permissions must be a list")
        member["permissions"] = permissions
    
    return member


def create_attachment_object(
    filename,
    storage_key,
    content_type=None,
    owner_id=None,
    size=None,
    organization_id=None
):
    """
    Create an attachment metadata object.
    
    Args:
        filename: Filename (string, required)
        storage_key: R2/S3 key or URL (string, required)
        content_type: MIME type (string)
        owner_id: Owner user ID (integer)
        size: File size in bytes (integer)
        organization_id: Organization ID (integer)
        
    Returns:
        dict: Attachment object
    """
    if not filename:
        raise ValueError("filename cannot be empty")
    
    if not storage_key:
        raise ValueError("storage_key cannot be empty")
    
    attachment = {
        "filename": filename,
        "storage_key": storage_key
    }
    
    if content_type is not None:
        attachment["content_type"] = content_type
    
    if owner_id is not None:
        if not isinstance(owner_id, int):
            raise ValueError("owner_id must be an integer")
        attachment["owner_id"] = owner_id
    
    if size is not None:
        if not isinstance(size, int) or size < 0:
            raise ValueError("size must be a non-negative integer")
        attachment["size"] = size
    
    if organization_id is not None:
        if not isinstance(organization_id, int):
            raise ValueError("organization_id must be an integer")
        attachment["organization_id"] = organization_id
    
    return attachment


def create_event_object(
    actor_id=None,
    object_type=None,
    object_temp_id=None,
    object_id=None,
    event_type=None,
    payload=None
):
    """
    Create an event (audit) object.
    
    Args:
        actor_id: User ID who performed the action (integer)
        object_type: Type of object ('district', 'area', 'road')
        object_temp_id: Temporary ID reference (string)
        object_id: Database ID (integer)
        event_type: Type of event ('create', 'update', 'delete')
        payload: Free-form JSON object
        
    Returns:
        dict: Event object
    """
    event = {}
    
    if actor_id is not None:
        if not isinstance(actor_id, int):
            raise ValueError("actor_id must be an integer")
        event["actor_id"] = actor_id
    
    if object_type is not None:
        event["object_type"] = object_type
    
    if object_temp_id is not None:
        event["object_temp_id"] = object_temp_id
    
    if object_id is not None:
        if not isinstance(object_id, int):
            raise ValueError("object_id must be an integer")
        event["object_id"] = object_id
    
    if event_type is not None:
        event["event_type"] = event_type
    
    if payload is not None:
        if not isinstance(payload, dict):
            raise ValueError("event payload must be a dictionary")
        event["payload"] = payload
    
    return event


def create_comprehensive_upload(
    district,
    areas=None,
    roads=None,
    district_members=None,
    attachments=None,
    events=None
):
    """
    Create a comprehensive district upload payload.
    
    This creates a single JSON object containing district, areas, roads,
    members, attachments, and events that can be uploaded in one transaction.
    Uses temporary IDs for client-side references.
    
    Args:
        district: District object (from create_district module)
        areas: List of area objects (created with create_area_object)
        roads: List of road objects (created with create_road_object)
        district_members: List of member objects (created with create_district_member_object)
        attachments: List of attachment objects (created with create_attachment_object)
        events: List of event objects (created with create_event_object)
        
    Returns:
        dict: Complete upload payload
    """
    if not district:
        raise ValueError("district object is required")
    
    # Validate district has required fields
    if 'key' not in district or 'name' not in district:
        raise ValueError("district must have 'key' and 'name' fields")
    
    upload = {
        "district": district
    }
    
    if areas is not None:
        if not isinstance(areas, list):
            raise ValueError("areas must be a list")
        upload["areas"] = areas
    
    if roads is not None:
        if not isinstance(roads, list):
            raise ValueError("roads must be a list")
        upload["roads"] = roads
    
    if district_members is not None:
        if not isinstance(district_members, list):
            raise ValueError("district_members must be a list")
        upload["district_members"] = district_members
    
    if attachments is not None:
        if not isinstance(attachments, list):
            raise ValueError("attachments must be a list")
        upload["attachments"] = attachments
    
    if events is not None:
        if not isinstance(events, list):
            raise ValueError("events must be a list")
        upload["events"] = events
    
    return upload


def save_upload_payload(upload, output_file):
    """
    Save the upload payload to a JSON file.
    
    Args:
        upload: Upload payload dictionary
        output_file: Path to output JSON file
    """
    with open(output_file, 'w') as f:
        json.dump(upload, f, indent=2)
    
    print(f"Saved upload payload to {output_file}")


def main():
    """Main execution function - demonstrates creating a comprehensive upload."""
    from create_district import create_district_from_geojson
    
    print("Creating comprehensive district upload example...")
    print()
    
    # Create the district
    district = create_district_from_geojson(
        'my_district.geojson',
        key='north-hills',
        name='North Hills',
        status='active',
        owner=42,
        created_by=42
    )
    
    # Create areas
    areas = [
        create_area_object(
            temp_id="area-1",
            name="North Hills - Sector A",
            area_border_coordinates={
                "type": "Polygon",
                "coordinates": [[
                    [-122.4230, 37.8267],
                    [-122.4230, 37.8217],
                    [-122.4180, 37.8217],
                    [-122.4180, 37.8267],
                    [-122.4230, 37.8267]
                ]]
            },
            status="active",
            sub_area=0,
            created_by=42
        ),
        create_area_object(
            temp_id="area-2",
            name="North Hills - Sector B",
            area_border_coordinates={
                "type": "Polygon",
                "coordinates": [[
                    [-122.4180, 37.8267],
                    [-122.4180, 37.8217],
                    [-122.4130, 37.8217],
                    [-122.4130, 37.8267],
                    [-122.4180, 37.8267]
                ]]
            },
            status="active",
            sub_area=0,
            created_by=42
        ),
        create_area_object(
            temp_id="area-2-1",
            name="North Hills - Sector B - Subarea 1",
            area_border_coordinates={
                "type": "Polygon",
                "coordinates": [[
                    [-122.4175, 37.8257],
                    [-122.4175, 37.8247],
                    [-122.4165, 37.8247],
                    [-122.4165, 37.8257],
                    [-122.4175, 37.8257]
                ]]
            },
            status="active",
            sub_area=1,
            created_by=42
        )
    ]
    
    # Create roads
    roads = [
        create_road_object(
            temp_id="road-1",
            key="nh-main-st",
            name="Main St",
            road_type="primary",
            length=1200.5,
            size="large",
            segments=[
                {"id": "seg-1", "from": [-122.4230, 37.8260], "to": [-122.4210, 37.8250], "length_m": 250.0},
                {"id": "seg-2", "from": [-122.4210, 37.8250], "to": [-122.4180, 37.8240], "length_m": 350.5}
            ],
            areas=["area-1"],
            coordinates={
                "type": "LineString",
                "coordinates": [
                    [-122.4230, 37.8260],
                    [-122.4210, 37.8250],
                    [-122.4180, 37.8240]
                ]
            }
        ),
        create_road_object(
            temp_id="road-2",
            key="nh-side-st",
            name="Side St",
            road_type="residential",
            length=300.0,
            size="small",
            segments=[
                {"id": "seg-1", "from": [-122.4170, 37.8255], "to": [-122.4160, 37.8250], "length_m": 100.0}
            ],
            areas=["area-2", "area-2-1"],
            coordinates={
                "type": "LineString",
                "coordinates": [
                    [-122.4170, 37.8255],
                    [-122.4160, 37.8250]
                ]
            }
        )
    ]
    
    # Create district members
    district_members = [
        create_district_member_object(user_id=42, role="admin", permissions=["manage_roads", "manage_areas"]),
        create_district_member_object(user_id=43, role="editor", permissions=["edit_roads"])
    ]
    
    # Create attachments
    attachments = [
        create_attachment_object(
            filename="thumbnail.png",
            storage_key="r2://bckt/thumbnail-nh.png",
            content_type="image/png",
            owner_id=42
        )
    ]
    
    # Create events
    events = [
        create_event_object(
            actor_id=42,
            object_type="district",
            event_type="create",
            payload={"note": "Imported full district with areas and roads"}
        )
    ]
    
    # Create comprehensive upload payload
    upload = create_comprehensive_upload(
        district=district,
        areas=areas,
        roads=roads,
        district_members=district_members,
        attachments=attachments,
        events=events
    )
    
    # Save to file
    save_upload_payload(upload, 'district_upload_comprehensive.json')
    
    print()
    print("Created comprehensive upload with:")
    print(f"  - 1 district")
    print(f"  - {len(areas)} areas (including {sum(1 for a in areas if a['sub_area'] == 1)} sub-areas)")
    print(f"  - {len(roads)} roads")
    print(f"  - {len(district_members)} district members")
    print(f"  - {len(attachments)} attachments")
    print(f"  - {len(events)} events")
    print()
    print("Done!")


if __name__ == '__main__':
    main()
