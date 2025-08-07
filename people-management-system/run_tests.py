#!/usr/bin/env python3
"""
Test runner script for the People Management System.

This script provides convenient ways to run different types of tests
with appropriate configurations and environment setup.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def run_command(cmd, description=""):
    """Run a shell command and handle errors."""
    if description:
        print(f"\n🔧 {description}")
    
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=project_root)
    
    if result.returncode != 0:
        print(f"❌ Command failed with exit code {result.returncode}")
        return False
    else:
        print(f"✅ {description or 'Command'} completed successfully")
        return True

def setup_test_environment():
    """Set up the test environment."""
    # Set environment variables for testing
    os.environ["TESTING"] = "true"
    os.environ["LOG_LEVEL"] = "INFO"
    
    # Ensure test database is clean
    test_db_path = project_root / "test.db"
    if test_db_path.exists():
        test_db_path.unlink()
    
    print("✅ Test environment set up")

def run_unit_tests():
    """Run unit tests only."""
    cmd = [
        "python", "-m", "pytest", 
        "tests/test_models.py",
        "tests/test_security.py",
        "-v", "--tb=short"
    ]
    return run_command(cmd, "Running unit tests")

def run_api_tests():
    """Run API integration tests."""
    cmd = [
        "python", "-m", "pytest",
        "tests/test_api_people.py", 
        "-v", "--tb=short"
    ]
    return run_command(cmd, "Running API tests")

def run_all_tests():
    """Run all tests with coverage."""
    cmd = [
        "python", "-m", "pytest",
        "tests/",
        "-v", "--tb=short",
        "--cov=server",
        "--cov-report=term-missing",
        "--cov-report=html:htmlcov"
    ]
    return run_command(cmd, "Running all tests with coverage")

def run_security_tests():
    """Run security-focused tests."""
    cmd = [
        "python", "-m", "pytest",
        "tests/test_security.py",
        "tests/test_api_people.py::TestPeopleAPIErrorHandling::test_sql_injection_prevention",
        "tests/test_api_people.py::TestPeopleAPIErrorHandling::test_xss_prevention",
        "-v", "--tb=short", "-k", "security or sanitiz or malicious"
    ]
    return run_command(cmd, "Running security tests")

def run_performance_tests():
    """Run performance tests."""
    cmd = [
        "python", "-m", "pytest",
        "tests/test_api_people.py::TestPeopleAPIPerformance",
        "-v", "--tb=short"
    ]
    return run_command(cmd, "Running performance tests")

def run_quick_tests():
    """Run a quick subset of tests for development."""
    cmd = [
        "python", "-m", "pytest",
        "tests/test_models.py::TestPersonModel::test_create_person_minimal",
        "tests/test_security.py::TestInputSanitizer::test_sanitize_string_basic",
        "tests/test_api_people.py::TestPeopleAPI::test_create_person_success",
        "-v", "--tb=short"
    ]
    return run_command(cmd, "Running quick development tests")

def check_dependencies():
    """Check that all required test dependencies are available."""
    required_packages = [
        "pytest",
        "pytest-cov", 
        "fastapi",
        "sqlalchemy",
        "httpx"
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"❌ Missing required packages: {', '.join(missing)}")
        print("Install with: pip install " + " ".join(missing))
        return False
    
    print("✅ All test dependencies available")
    return True

def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(
        description="Test runner for People Management System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python run_tests.py --all          # Run all tests with coverage
    python run_tests.py --unit         # Run only unit tests  
    python run_tests.py --api          # Run only API tests
    python run_tests.py --security     # Run security-focused tests
    python run_tests.py --performance  # Run performance tests
    python run_tests.py --quick        # Run quick development tests
        """
    )
    
    parser.add_argument("--all", action="store_true", help="Run all tests")
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--api", action="store_true", help="Run API tests only")
    parser.add_argument("--security", action="store_true", help="Run security tests")
    parser.add_argument("--performance", action="store_true", help="Run performance tests")
    parser.add_argument("--quick", action="store_true", help="Run quick development tests")
    parser.add_argument("--check-deps", action="store_true", help="Check test dependencies")
    
    args = parser.parse_args()
    
    # If no specific test type is chosen, run all tests
    if not any([args.all, args.unit, args.api, args.security, args.performance, args.quick, args.check_deps]):
        args.all = True
    
    print("🧪 People Management System Test Runner")
    print("=" * 50)
    
    # Check dependencies first
    if not check_dependencies():
        return 1
    
    if args.check_deps:
        return 0
    
    # Set up test environment
    setup_test_environment()
    
    success = True
    
    try:
        if args.quick:
            success &= run_quick_tests()
        elif args.unit:
            success &= run_unit_tests()
        elif args.api:
            success &= run_api_tests()
        elif args.security:
            success &= run_security_tests()
        elif args.performance:
            success &= run_performance_tests()
        elif args.all:
            success &= run_all_tests()
    
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Test runner error: {e}")
        return 1
    
    if success:
        print("\n🎉 All tests completed successfully!")
        return 0
    else:
        print("\n💥 Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())