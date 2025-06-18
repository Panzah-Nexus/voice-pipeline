#!/usr/bin/env python3
"""Simple test runner for voice pipeline project."""

import subprocess
import sys
import os
import argparse

def run_test(test_name):
    """Run a specific test."""
    test_map = {
        'piper': 'tests.test_piper_local',
        'docker': 'tests.test_docker_build',
        'all': None
    }
    
    if test_name not in test_map:
        print(f"❌ Unknown test: {test_name}")
        print(f"Available tests: {', '.join(test_map.keys())}")
        return False
    
    if test_name == 'all':
        # Run all tests
        success = True
        for t in ['piper', 'docker']:
            print(f"\n{'='*50}")
            print(f"Running {t} test...")
            print('='*50)
            if not run_test(t):
                success = False
        return success
    
    # Run specific test
    module = test_map[test_name]
    cmd = [sys.executable, '-m', module]
    
    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error running test: {e}")
        return False

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Run voice pipeline tests')
    parser.add_argument(
        'test',
        nargs='?',
        default='all',
        choices=['piper', 'docker', 'all'],
        help='Test to run (default: all)'
    )
    
    args = parser.parse_args()
    
    print("🧪 Voice Pipeline Test Runner")
    print("="*50)
    
    # Ensure we're in the right directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    success = run_test(args.test)
    
    if success:
        print("\n✅ Tests completed successfully!")
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main() 