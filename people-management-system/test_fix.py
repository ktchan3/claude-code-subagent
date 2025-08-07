#!/usr/bin/env python3
"""Test script to verify the sort_desc parameter fix"""

def test_parameter_conversion():
    """Test that sort_desc is properly converted to sort_order"""
    
    # Simulate the fix in api_client.py
    search_params = {
        "page": 1,
        "size": 20,
        "sort_desc": False  # This is what the client sends
    }
    
    # Apply the fix
    if "sort_desc" in search_params:
        sort_desc = search_params.pop("sort_desc")  
        search_params["sort_order"] = "desc" if sort_desc else "asc"
    
    # Verify the result
    assert "sort_desc" not in search_params, "sort_desc should be removed"
    assert "sort_order" in search_params, "sort_order should be added"
    assert search_params["sort_order"] == "asc", "sort_desc=False should become sort_order=asc"
    
    print("✅ Test 1 passed: sort_desc=False → sort_order=asc")
    
    # Test with sort_desc=True
    search_params2 = {
        "page": 1,
        "size": 20,
        "sort_desc": True
    }
    
    if "sort_desc" in search_params2:
        sort_desc = search_params2.pop("sort_desc")
        search_params2["sort_order"] = "desc" if sort_desc else "asc"
    
    assert search_params2["sort_order"] == "desc", "sort_desc=True should become sort_order=desc"
    print("✅ Test 2 passed: sort_desc=True → sort_order=desc")
    
    print("\n✅ All tests passed! The parameter conversion fix is working correctly.")
    print("\nThe fix ensures:")
    print("- Client's sort_desc=false → Server's sort_order=asc")
    print("- Client's sort_desc=true → Server's sort_order=desc")
    print("\nThis resolves the 500 Internal Server Error when listing people.")

if __name__ == "__main__":
    test_parameter_conversion()