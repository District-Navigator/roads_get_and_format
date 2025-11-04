#!/usr/bin/env python3
"""
Test script for create_district_upload.py
Tests comprehensive district upload creation with nested entities
"""

import json
import sys
from create_district_upload import (
    create_area_object,
    create_road_object,
    create_district_member_object,
    create_attachment_object,
    create_event_object,
    create_comprehensive_upload
)


def test_area_object_creation():
    """Test creating area objects"""
    print("Testing area object creation...")
    
    # Test basic area
    area = create_area_object(
        temp_id="area-1",
        name="Test Area",
        status="active",
        sub_area=0,
        created_by=42
    )
    
    if area["temp_id"] != "area-1":
        print(f"  ✗ temp_id mismatch: {area['temp_id']}")
        return False
    
    if area["name"] != "Test Area":
        print(f"  ✗ name mismatch: {area['name']}")
        return False
    
    if area["sub_area"] != 0:
        print(f"  ✗ sub_area should be 0: {area['sub_area']}")
        return False
    
    print("  ✓ Basic area created successfully")
    
    # Test sub-area
    sub_area = create_area_object(
        temp_id="area-1-1",
        name="Test Sub-Area",
        sub_area=1
    )
    
    if sub_area["sub_area"] != 1:
        print(f"  ✗ sub_area should be 1: {sub_area['sub_area']}")
        return False
    
    print("  ✓ Sub-area created successfully")
    
    # Test area with coordinates
    area_with_coords = create_area_object(
        temp_id="area-2",
        name="Area with Coords",
        area_border_coordinates={
            "type": "Polygon",
            "coordinates": [[
                [-122.4, 37.8],
                [-122.4, 37.7],
                [-122.3, 37.7],
                [-122.3, 37.8],
                [-122.4, 37.8]
            ]]
        }
    )
    
    if "area_border_coordinates" not in area_with_coords:
        print("  ✗ area_border_coordinates not found")
        return False
    
    print("  ✓ Area with coordinates created successfully")
    
    # Test validation - empty name
    try:
        create_area_object(temp_id="bad", name="")
        print("  ✗ Empty name accepted")
        return False
    except ValueError:
        print("  ✓ Empty name rejected")
    
    # Test validation - invalid sub_area
    try:
        create_area_object(temp_id="bad", name="Test", sub_area=2)
        print("  ✗ Invalid sub_area accepted")
        return False
    except ValueError:
        print("  ✓ Invalid sub_area rejected")
    
    print("✓ All area object tests passed!\n")
    return True


def test_road_object_creation():
    """Test creating road objects"""
    print("Testing road object creation...")
    
    # Test basic road
    road = create_road_object(
        temp_id="road-1",
        key="main-st",
        name="Main Street",
        road_type="primary",
        length=1200.5,
        size="large"
    )
    
    if road["temp_id"] != "road-1":
        print(f"  ✗ temp_id mismatch: {road['temp_id']}")
        return False
    
    if road["key"] != "main-st":
        print(f"  ✗ key mismatch: {road['key']}")
        return False
    
    if road["type"] != "primary":
        print(f"  ✗ type mismatch: {road['type']}")
        return False
    
    print("  ✓ Basic road created successfully")
    
    # Test road with segments
    road_with_segments = create_road_object(
        temp_id="road-2",
        key="side-st",
        name="Side Street",
        segments=[
            {"id": "seg-1", "from": [-122.4, 37.8], "to": [-122.3, 37.7], "length_m": 100.0}
        ]
    )
    
    if "segments" not in road_with_segments:
        print("  ✗ segments not found")
        return False
    
    if len(road_with_segments["segments"]) != 1:
        print(f"  ✗ wrong number of segments: {len(road_with_segments['segments'])}")
        return False
    
    print("  ✓ Road with segments created successfully")
    
    # Test road with areas
    road_with_areas = create_road_object(
        temp_id="road-3",
        key="cross-st",
        name="Cross Street",
        areas=["area-1", "area-2"]
    )
    
    if "areas" not in road_with_areas:
        print("  ✗ areas not found")
        return False
    
    if road_with_areas["areas"] != ["area-1", "area-2"]:
        print(f"  ✗ areas mismatch: {road_with_areas['areas']}")
        return False
    
    print("  ✓ Road with area references created successfully")
    
    # Test road with coordinates
    road_with_coords = create_road_object(
        temp_id="road-4",
        key="line-st",
        name="Line Street",
        coordinates={
            "type": "LineString",
            "coordinates": [
                [-122.4, 37.8],
                [-122.3, 37.7]
            ]
        }
    )
    
    if "coordinates" not in road_with_coords:
        print("  ✗ coordinates not found")
        return False
    
    print("  ✓ Road with coordinates created successfully")
    
    # Test validation - empty key
    try:
        create_road_object(temp_id="bad", key="", name="Test")
        print("  ✗ Empty key accepted")
        return False
    except ValueError:
        print("  ✓ Empty key rejected")
    
    # Test validation - uppercase key
    try:
        create_road_object(temp_id="bad", key="MAIN-ST", name="Test")
        print("  ✗ Uppercase key accepted")
        return False
    except ValueError:
        print("  ✓ Uppercase key rejected")
    
    # Test validation - invalid size
    try:
        create_road_object(temp_id="bad", key="test", name="Test", size="huge")
        print("  ✗ Invalid size accepted")
        return False
    except ValueError:
        print("  ✓ Invalid size rejected")
    
    print("✓ All road object tests passed!\n")
    return True


def test_district_member_creation():
    """Test creating district member objects"""
    print("Testing district member creation...")
    
    # Test basic member
    member = create_district_member_object(user_id=42, role="member")
    
    if member["user_id"] != 42:
        print(f"  ✗ user_id mismatch: {member['user_id']}")
        return False
    
    if member["role"] != "member":
        print(f"  ✗ role mismatch: {member['role']}")
        return False
    
    print("  ✓ Basic member created successfully")
    
    # Test admin with permissions
    admin = create_district_member_object(
        user_id=1,
        role="admin",
        permissions=["manage_roads", "manage_areas"]
    )
    
    if "permissions" not in admin:
        print("  ✗ permissions not found")
        return False
    
    if admin["permissions"] != ["manage_roads", "manage_areas"]:
        print(f"  ✗ permissions mismatch: {admin['permissions']}")
        return False
    
    print("  ✓ Admin with permissions created successfully")
    
    # Test validation - non-integer user_id
    try:
        create_district_member_object(user_id="not-an-int")
        print("  ✗ Non-integer user_id accepted")
        return False
    except ValueError:
        print("  ✓ Non-integer user_id rejected")
    
    print("✓ All district member tests passed!\n")
    return True


def test_attachment_creation():
    """Test creating attachment objects"""
    print("Testing attachment creation...")
    
    # Test basic attachment
    attachment = create_attachment_object(
        filename="test.png",
        storage_key="r2://bucket/test.png"
    )
    
    if attachment["filename"] != "test.png":
        print(f"  ✗ filename mismatch: {attachment['filename']}")
        return False
    
    if attachment["storage_key"] != "r2://bucket/test.png":
        print(f"  ✗ storage_key mismatch: {attachment['storage_key']}")
        return False
    
    print("  ✓ Basic attachment created successfully")
    
    # Test attachment with metadata
    attachment_with_meta = create_attachment_object(
        filename="doc.pdf",
        storage_key="s3://bucket/doc.pdf",
        content_type="application/pdf",
        owner_id=42,
        size=1024
    )
    
    if attachment_with_meta["content_type"] != "application/pdf":
        print(f"  ✗ content_type mismatch")
        return False
    
    if attachment_with_meta["owner_id"] != 42:
        print(f"  ✗ owner_id mismatch")
        return False
    
    if attachment_with_meta["size"] != 1024:
        print(f"  ✗ size mismatch")
        return False
    
    print("  ✓ Attachment with metadata created successfully")
    
    # Test validation - empty filename
    try:
        create_attachment_object(filename="", storage_key="test")
        print("  ✗ Empty filename accepted")
        return False
    except ValueError:
        print("  ✓ Empty filename rejected")
    
    print("✓ All attachment tests passed!\n")
    return True


def test_event_creation():
    """Test creating event objects"""
    print("Testing event creation...")
    
    # Test basic event
    event = create_event_object(
        actor_id=42,
        object_type="district",
        event_type="create"
    )
    
    if event["actor_id"] != 42:
        print(f"  ✗ actor_id mismatch: {event['actor_id']}")
        return False
    
    if event["object_type"] != "district":
        print(f"  ✗ object_type mismatch: {event['object_type']}")
        return False
    
    print("  ✓ Basic event created successfully")
    
    # Test event with payload
    event_with_payload = create_event_object(
        actor_id=1,
        object_type="road",
        event_type="update",
        payload={"note": "Updated road data"}
    )
    
    if "payload" not in event_with_payload:
        print("  ✗ payload not found")
        return False
    
    if event_with_payload["payload"]["note"] != "Updated road data":
        print(f"  ✗ payload mismatch")
        return False
    
    print("  ✓ Event with payload created successfully")
    
    print("✓ All event tests passed!\n")
    return True


def test_comprehensive_upload():
    """Test creating comprehensive upload payload"""
    print("Testing comprehensive upload creation...")
    
    from create_district import create_district_object
    
    # Create district
    district = create_district_object(
        key="test-district",
        name="Test District",
        status="active"
    )
    
    # Create areas
    areas = [
        create_area_object(temp_id="area-1", name="Area 1"),
        create_area_object(temp_id="area-2", name="Area 2")
    ]
    
    # Create roads
    roads = [
        create_road_object(temp_id="road-1", key="road-1", name="Road 1", areas=["area-1"]),
        create_road_object(temp_id="road-2", key="road-2", name="Road 2", areas=["area-1", "area-2"])
    ]
    
    # Create members
    members = [
        create_district_member_object(user_id=42, role="admin")
    ]
    
    # Create attachments
    attachments = [
        create_attachment_object(filename="test.png", storage_key="r2://test")
    ]
    
    # Create events
    events = [
        create_event_object(actor_id=42, object_type="district", event_type="create")
    ]
    
    # Create comprehensive upload
    upload = create_comprehensive_upload(
        district=district,
        areas=areas,
        roads=roads,
        district_members=members,
        attachments=attachments,
        events=events
    )
    
    # Validate structure
    if "district" not in upload:
        print("  ✗ district not found in upload")
        return False
    
    if "areas" not in upload or len(upload["areas"]) != 2:
        print("  ✗ areas not found or wrong count")
        return False
    
    if "roads" not in upload or len(upload["roads"]) != 2:
        print("  ✗ roads not found or wrong count")
        return False
    
    if "district_members" not in upload or len(upload["district_members"]) != 1:
        print("  ✗ district_members not found or wrong count")
        return False
    
    if "attachments" not in upload or len(upload["attachments"]) != 1:
        print("  ✗ attachments not found or wrong count")
        return False
    
    if "events" not in upload or len(upload["events"]) != 1:
        print("  ✗ events not found or wrong count")
        return False
    
    print("  ✓ Comprehensive upload structure validated")
    
    # Test JSON serialization
    try:
        json_str = json.dumps(upload, indent=2)
        parsed = json.loads(json_str)
        print("  ✓ Upload is JSON-serializable")
    except Exception as e:
        print(f"  ✗ JSON serialization failed: {e}")
        return False
    
    # Test validation - missing district
    try:
        create_comprehensive_upload(district=None)
        print("  ✗ Missing district accepted")
        return False
    except ValueError:
        print("  ✓ Missing district rejected")
    
    print("✓ All comprehensive upload tests passed!\n")
    return True


def main():
    """Run all tests"""
    print("=" * 60)
    print("Running Comprehensive District Upload Tests")
    print("=" * 60 + "\n")
    
    results = []
    
    results.append(("Area Objects", test_area_object_creation()))
    results.append(("Road Objects", test_road_object_creation()))
    results.append(("District Members", test_district_member_creation()))
    results.append(("Attachments", test_attachment_creation()))
    results.append(("Events", test_event_creation()))
    results.append(("Comprehensive Upload", test_comprehensive_upload()))
    
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
