#!/usr/bin/env python3
"""
Test script for create_district_sql.py
Tests SQL query generation for district creation
"""

import sys
from create_district_sql import generate_district_insert_query


def test_basic_query_generation():
    """Test basic SQL query generation"""
    print("Testing basic SQL query generation...")
    
    query = generate_district_insert_query("North Hills", 42, 42)
    
    # Check that query contains expected elements
    expected_elements = [
        "INSERT INTO districts",
        "name, created_by, owner",
        "VALUES",
        "'North Hills'",
        "42",
    ]
    
    all_found = True
    for element in expected_elements:
        if element in query:
            print(f"  ✓ Query contains '{element}'")
        else:
            print(f"  ✗ Query missing '{element}'")
            all_found = False
    
    if all_found:
        print("  ✓ Query structure is correct")
        print(f"  Generated query:\n{query}")
        print("✓ Basic query generation test passed!\n")
        return True
    else:
        print("✗ Basic query generation test failed\n")
        return False


def test_different_user_ids():
    """Test with different created_by and owner IDs"""
    print("Testing with different user IDs...")
    
    query = generate_district_insert_query("Downtown District", 10, 20)
    
    if "'Downtown District'" in query and "10" in query and "20" in query:
        print("  ✓ Query contains correct user IDs")
        print(f"  Generated query:\n{query}")
        print("✓ Different user IDs test passed!\n")
        return True
    else:
        print("  ✗ Query missing expected user IDs")
        print("✗ Different user IDs test failed\n")
        return False


def test_name_with_special_characters():
    """Test district name with special characters"""
    print("Testing name with special characters...")
    
    # Test with single quote in name (SQL injection prevention)
    query = generate_district_insert_query("O'Brien District", 1, 1)
    
    if "O''Brien District" in query:
        print("  ✓ Single quotes properly escaped")
        print(f"  Generated query:\n{query}")
        print("✓ Special characters test passed!\n")
        return True
    else:
        print("  ✗ Single quotes not properly escaped")
        print("✗ Special characters test failed\n")
        return False


def test_string_to_int_conversion():
    """Test that string inputs for user IDs are converted to integers"""
    print("Testing string to int conversion...")
    
    try:
        query = generate_district_insert_query("Test District", "5", "10")
        
        if "5" in query and "10" in query:
            print("  ✓ String user IDs converted to integers")
            print(f"  Generated query:\n{query}")
            print("✓ String to int conversion test passed!\n")
            return True
        else:
            print("  ✗ User IDs not found in query")
            print("✗ String to int conversion test failed\n")
            return False
    except Exception as e:
        print(f"  ✗ Unexpected error: {e}")
        print("✗ String to int conversion test failed\n")
        return False


def test_error_handling():
    """Test error handling for invalid inputs"""
    print("Testing error handling...")
    
    # Test empty name
    try:
        generate_district_insert_query("", 1, 1)
        print("  ✗ Empty name accepted")
        return False
    except ValueError:
        print("  ✓ Empty name rejected")
    
    # Test whitespace-only name
    try:
        generate_district_insert_query("   ", 1, 1)
        print("  ✗ Whitespace-only name accepted")
        return False
    except ValueError:
        print("  ✓ Whitespace-only name rejected")
    
    # Test invalid created_by
    try:
        generate_district_insert_query("Test", "not-a-number", 1)
        print("  ✗ Invalid created_by accepted")
        return False
    except ValueError:
        print("  ✓ Invalid created_by rejected")
    
    # Test invalid owner
    try:
        generate_district_insert_query("Test", 1, "not-a-number")
        print("  ✗ Invalid owner accepted")
        return False
    except ValueError:
        print("  ✓ Invalid owner rejected")
    
    print("✓ All error handling tests passed!\n")
    return True


def test_query_format():
    """Test that query follows proper SQL format"""
    print("Testing SQL query format...")
    
    query = generate_district_insert_query("Station 8", 42, 42)
    
    # Check query starts with INSERT
    if query.strip().startswith("INSERT INTO districts"):
        print("  ✓ Query starts with INSERT INTO districts")
    else:
        print("  ✗ Query does not start correctly")
        return False
    
    # Check query ends with semicolon
    if query.strip().endswith(";"):
        print("  ✓ Query ends with semicolon")
    else:
        print("  ✗ Query does not end with semicolon")
        return False
    
    # Check VALUES clause exists
    if "VALUES" in query:
        print("  ✓ Query contains VALUES clause")
    else:
        print("  ✗ Query missing VALUES clause")
        return False
    
    print("✓ SQL query format test passed!\n")
    return True


def main():
    """Run all tests"""
    print("=" * 60)
    print("Running SQL Query Generation Tests")
    print("=" * 60 + "\n")
    
    results = []
    
    results.append(("Basic Query Generation", test_basic_query_generation()))
    results.append(("Different User IDs", test_different_user_ids()))
    results.append(("Special Characters", test_name_with_special_characters()))
    results.append(("String to Int Conversion", test_string_to_int_conversion()))
    results.append(("Error Handling", test_error_handling()))
    results.append(("Query Format", test_query_format()))
    
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
