# District Object Creation - Quick Reference Guide

This guide provides quick examples for creating district objects that match database schema requirements.

## Basic Usage

### 1. Create a minimal district (required fields only)

```python
from create_district import create_district_from_geojson

district = create_district_from_geojson(
    'my_district.geojson',
    minimal=True
)
# Output: {"key": "my-district", "name": "My District"}
```

### 2. Create a full district (all fields)

```python
from create_district import create_district_from_geojson

district = create_district_from_geojson(
    'my_district.geojson',
    key='north-hills',
    name='North Hills',
    status='active',
    road_count=0,
    owner=42,
    created_by=42
)
```

### 3. Create from scratch (without GeoJSON file)

```python
from create_district import create_district_object

district = create_district_object(
    key='downtown',
    name='Downtown District',
    status='active',
    road_count=150
)
```

### 4. Command line usage

```bash
# Run the default example
python create_district.py

# This creates two files:
# - district_minimal.json (required fields only)
# - district_full.json (all fields)
```

## Field Reference

### Required Fields
- `key` (string): Unique slug identifier (lowercase, alphanumeric, hyphens)
- `name` (string): Human-readable name

### Optional Fields
- `status` (string): One of 'active', 'archived', 'disabled' (default: 'active')
- `road_count` (integer): Number of roads (default: 0, must be non-negative)
- `district_border_coordinates` (GeoJSON): Polygon or MultiPolygon with [lng, lat] coordinates
- `owner` (integer): User ID of the owner (foreign key to users.id)
- `created_by` (integer): User ID of creator (foreign key to users.id)

### DB-Managed Fields (do not include in create payloads)
- `id`: Auto-generated primary key
- `created_at`: Auto-set timestamp
- `updated_at`: Auto-updated timestamp
- `deleted_at`: For soft-deletes

## Validation Rules

### Key Validation
- Must be non-empty
- Must be lowercase
- Can only contain: a-z, 0-9, hyphen (-)
- Maximum 255 characters
- Must be unique across all districts

### Name Validation
- Must be non-empty
- Maximum 255 characters

### Status Validation
- Must be one of: 'active', 'archived', 'disabled'

### Road Count Validation
- Must be a non-negative integer

### GeoJSON Validation
- Must be a Polygon or MultiPolygon
- Coordinates must be in [longitude, latitude] format
- Polygon rings must be closed (first point = last point)
- Must have at least 4 coordinates per ring

### Foreign Key Validation
- `owner` and `created_by` must be integers if provided
- Should reference existing user IDs in the database

## API Usage Example

```python
from create_district import create_district_from_geojson, save_district_object
import requests

# Create the district object
district = create_district_from_geojson(
    'my_district.geojson',
    key='my-district',
    name='My District',
    status='active',
    owner=42,
    created_by=42
)

# Save to file (optional)
save_district_object(district, 'district_to_upload.json')

# Upload to API
response = requests.post(
    'https://api.example.com/districts',
    json=district,
    headers={'Content-Type': 'application/json'}
)

if response.status_code == 201:
    created_district = response.json()
    print(f"Created district with ID: {created_district['id']}")
else:
    print(f"Error: {response.status_code} - {response.text}")
```

## Expected API Responses

### Success (201 Created)
```json
{
  "id": 1,
  "key": "north-hills",
  "name": "North Hills",
  "status": "active",
  "road_count": 0,
  "district_border_coordinates": {...},
  "owner": 42,
  "created_by": 42,
  "created_at": "2025-11-04T12:34:56.789Z",
  "updated_at": "2025-11-04T12:34:56.789Z",
  "deleted_at": null
}
```

### Error: Duplicate Key (409 Conflict)
```json
{
  "error": "Duplicate key",
  "message": "A district with key 'north-hills' already exists"
}
```

### Error: Invalid Foreign Key (400 Bad Request)
```json
{
  "error": "Invalid reference",
  "message": "User with id 42 does not exist"
}
```

## Utilities

### Auto-generate slug from name

```python
from create_district import slugify

slug = slugify("North Hills District")
# Result: "north-hills-district"
```

### Validate fields

```python
from create_district import (
    validate_district_key,
    validate_district_name,
    validate_status,
    validate_geojson_polygon
)

try:
    validate_district_key("north-hills")
    validate_district_name("North Hills")
    validate_status("active")
    print("All validations passed!")
except ValueError as e:
    print(f"Validation error: {e}")
```

## Testing

Run the test suite:

```bash
# Unit tests
python test_create_district.py

# Integration test
python test_integration.py
```

## Common Issues

### Issue: "District key must contain only lowercase letters..."
**Solution**: Use the `slugify()` function to convert names to valid keys

### Issue: "Polygon ring must be closed..."
**Solution**: Ensure GeoJSON polygons have first coordinate = last coordinate

### Issue: "User with id X does not exist"
**Solution**: Verify the user ID exists before setting `owner` or `created_by`

### Issue: "Duplicate key error"
**Solution**: Choose a unique key or query the database first to check uniqueness
