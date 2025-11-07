#!/usr/bin/env python3
"""
Create District Member SQL Query Generator
Generates SQL INSERT queries for adding district members to the database.
Takes inputs: district_id, user_id
"""

import argparse
import sys

# ============================================================================
# INPUT VARIABLES - Edit these values when running in PyCharm/IDE
# ============================================================================
DISTRICT_ID = 2
USER_ID = 1
# ============================================================================


def generate_district_member_insert_query(district_id, user_id):
    """
    Generate an SQL INSERT query for adding a district member to the database.
    
    Args:
        district_id: District ID (INTEGER, FK to districts.id)
        user_id: User ID (INTEGER, FK to users.id)
        
    Returns:
        str: SQL INSERT query
    """
    # Validate inputs
    if not isinstance(district_id, int):
        try:
            district_id = int(district_id)
        except (ValueError, TypeError):
            raise ValueError("district_id must be an integer")
    
    if not isinstance(user_id, int):
        try:
            user_id = int(user_id)
        except (ValueError, TypeError):
            raise ValueError("user_id must be an integer")
    
    # Generate SQL query
    # The database schema has defaults for role, permissions, updated_at, deleted_at
    # We explicitly set joined_at to datetime('now') and active to 1
    query = f"""INSERT INTO district_members (district_id, user_id, joined_at, active)
VALUES ({district_id}, {user_id}, datetime('now'), 1);"""
    
    return query


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description='Generate SQL INSERT query for adding a district member'
    )
    parser.add_argument(
        'district_id',
        type=int,
        nargs='?',  # Make positional argument optional
        default=None,
        help='District ID (FK to districts.id)'
    )
    parser.add_argument(
        'user_id',
        type=int,
        nargs='?',  # Make positional argument optional
        default=None,
        help='User ID (FK to users.id)'
    )
    
    args = parser.parse_args()
    
    # Use command-line arguments if provided, otherwise use variables from top of file
    district_id = args.district_id if args.district_id is not None else DISTRICT_ID
    user_id = args.user_id if args.user_id is not None else USER_ID
    
    try:
        query = generate_district_member_insert_query(district_id, user_id)
        print(query)
        return 0
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
