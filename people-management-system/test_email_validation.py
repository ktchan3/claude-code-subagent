#!/usr/bin/env python3
"""
Test script to verify email validation allows periods and other valid characters.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtGui import QValidator
from client.ui.widgets.person_form import EmailValidator


def test_email_validation():
    """Test that email validation allows periods and other characters."""
    print("\n" + "="*60)
    print("🧪 Testing Email Validation Fix")
    print("="*60)
    
    validator = EmailValidator()
    
    # Test cases: (input, expected_state, description)
    test_cases = [
        ("", QValidator.Intermediate, "Empty input"),
        ("j", QValidator.Intermediate, "Single letter"),
        ("john", QValidator.Intermediate, "Name without @"),
        ("john.", QValidator.Intermediate, "Name with period"),
        ("john.d", QValidator.Intermediate, "Name with period and letter"),
        ("john.doe", QValidator.Intermediate, "Full name with period"),
        ("john.doe@", QValidator.Intermediate, "Name with @ but no domain"),
        ("john.doe@e", QValidator.Intermediate, "Partial domain"),
        ("john.doe@ex", QValidator.Intermediate, "More partial domain"),
        ("john.doe@example", QValidator.Intermediate, "Domain without extension"),
        ("john.doe@example.", QValidator.Intermediate, "Domain with period"),
        ("john.doe@example.c", QValidator.Intermediate, "Partial extension"),
        ("john.doe@example.com", QValidator.Acceptable, "Complete valid email"),
        ("user.name+tag@example.co.uk", QValidator.Acceptable, "Complex valid email"),
        ("test_email.123@sub.domain.com", QValidator.Acceptable, "Email with underscore and subdomain"),
        ("john doe@example.com", QValidator.Invalid, "Email with space (invalid)"),
        ("john[doe]@example.com", QValidator.Invalid, "Email with brackets (invalid)"),
    ]
    
    print("\n📧 Testing email validation scenarios:")
    print("-" * 60)
    
    all_passed = True
    
    for input_text, expected_state, description in test_cases:
        state, _, _ = validator.validate(input_text, len(input_text))
        
        # Convert state to string for display
        state_names = {
            QValidator.Invalid: "Invalid",
            QValidator.Intermediate: "Intermediate",
            QValidator.Acceptable: "Acceptable"
        }
        
        state_name = state_names.get(state, "Unknown")
        expected_name = state_names.get(expected_state, "Unknown")
        
        if state == expected_state:
            print(f"✅ '{input_text}' → {state_name} ({description})")
        else:
            print(f"❌ '{input_text}' → {state_name}, expected {expected_name} ({description})")
            all_passed = False
    
    # Special test: Progressive typing of an email with periods
    print("\n📝 Testing progressive typing of 'john.doe@example.com':")
    print("-" * 60)
    
    email = "john.doe@example.com"
    progressive_input = ""
    typing_success = True
    
    for char in email:
        progressive_input += char
        state, _, _ = validator.validate(progressive_input, len(progressive_input))
        
        if state == QValidator.Invalid:
            print(f"❌ Blocked at '{progressive_input}' - Cannot type '{char}'!")
            typing_success = False
            break
        else:
            state_name = "Intermediate" if state == QValidator.Intermediate else "Acceptable"
            print(f"✅ '{progressive_input}' → {state_name}")
    
    if typing_success:
        print("\n✅ Successfully typed entire email with periods!")
    else:
        print("\n❌ Email typing was blocked!")
        all_passed = False
    
    # Summary
    print("\n" + "="*60)
    print("📊 Test Summary")
    print("="*60)
    
    if all_passed:
        print("\n✅ All email validation tests passed!")
        print("\n🎉 The email field now allows:")
        print("   • Periods (.) anywhere in the email")
        print("   • Underscores (_)")
        print("   • Plus signs (+)")
        print("   • Hyphens (-)")
        print("   • All valid email characters")
        print("\n💡 Users can now enter email addresses smoothly without blocking!")
    else:
        print("\n❌ Some tests failed - check the output above")
    
    print("="*60 + "\n")
    
    return all_passed


if __name__ == "__main__":
    try:
        success = test_email_validation()
        sys.exit(0 if success else 1)
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Note: This test requires PySide6 to be installed")
        sys.exit(1)