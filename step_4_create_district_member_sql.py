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


def validate_positive_integer(value, param_name):
    """
    Validate that a value is a positive integer.
    
    Args:
        value: Value to validate
        param_name: Parameter name for error messages
        
    Returns:
        int: Validated integer value
        
    Raises:
        ValueError: If value is not a positive integer
    """
    if not isinstance(value, int):
        try:
            value = int(value)
        except (ValueError, TypeError):
            raise ValueError(f"{param_name} must be an integer")
    
    if value <= 0:
        raise ValueError(f"{param_name} must be a positive integer (got {value})")
    
    return value


def generate_district_member_insert_query(district_id, user_id):
    """
    Generate an SQL INSERT query for adding a district member to the database.
    
    Args:
        district_id: District ID (INTEGER, FK to districts.id)
        user_id: User ID (INTEGER, FK to users.id)
        
    Returns:
        str: SQL INSERT query
    """
    # Validate inputs as positive integers
    district_id = validate_positive_integer(district_id, "district_id")
    user_id = validate_positive_integer(user_id, "user_id")
    
    # Generate SQL query
    # The database schema has defaults for role, permissions, updated_at, deleted_at
    # We explicitly set joined_at to datetime('now') and active to 1
    # Using str() to be explicit about converting validated integers to strings
    query = f"""INSERT INTO district_members (district_id, user_id, joined_at, active)
VALUES ({str(district_id)}, {str(user_id)}, datetime('now'), 1);"""
    
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
