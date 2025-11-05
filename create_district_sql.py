#!/usr/bin/env python3
"""
Create District SQL Query Generator
Generates SQL INSERT queries for adding districts to the database.
Takes inputs: name, created_by, owner
"""

import argparse
import sys
from datetime import datetime


def generate_district_insert_query(name, created_by, owner):
    """
    Generate an SQL INSERT query for adding a district to the database.
    
    Args:
        name: District name (TEXT, required)
        created_by: User ID who created the district (INTEGER, FK to users.id)
        owner: Owner user ID (INTEGER, FK to users.id)
        
    Returns:
        str: SQL INSERT query
    """
    # Validate inputs
    if not name or not name.strip():
        raise ValueError("District name cannot be empty")
    
    if not isinstance(created_by, int):
        try:
            created_by = int(created_by)
        except (ValueError, TypeError):
            raise ValueError("created_by must be an integer (user ID)")
    
    if not isinstance(owner, int):
        try:
            owner = int(owner)
        except (ValueError, TypeError):
            raise ValueError("owner must be an integer (user ID)")
    
    # Escape single quotes in name
    escaped_name = name.replace("'", "''")
    
    # Generate SQL query
    # The database schema has defaults for status, road_count, created_at, updated_at
    # We only need to provide: name, created_by, owner
    query = f"""INSERT INTO districts (name, created_by, owner)
VALUES ('{escaped_name}', {created_by}, {owner});"""
    
    return query


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description='Generate SQL INSERT query for creating a district'
    )
    parser.add_argument(
        'name',
        type=str,
        help='District name'
    )
    parser.add_argument(
        'created_by',
        type=int,
        help='User ID of the creator (FK to users.id)'
    )
    parser.add_argument(
        'owner',
        type=int,
        help='User ID of the owner (FK to users.id)'
    )
    
    args = parser.parse_args()
    
    try:
        query = generate_district_insert_query(args.name, args.created_by, args.owner)
        print(query)
        return 0
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
