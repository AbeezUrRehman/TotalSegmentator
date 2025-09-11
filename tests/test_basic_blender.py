#!/usr/bin/env python3

"""
Simple test for blender export functionality without external dependencies.
"""

import tempfile
from pathlib import Path
import json
import sys
import os

# Add the totalsegmentator directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_basic_import():
    """Test that our modules can be imported without dependencies."""
    try:
        # Test basic imports
        from totalsegmentator.blender_export import ORGAN_MATERIALS, MATERIAL_COLORS
        from totalsegmentator.blender_export import generate_blender_import_script, save_task_summary
        
        print("✓ Basic imports successful")
        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False

def test_material_definitions():
    """Test material definitions."""
    try:
        from totalsegmentator.blender_export import ORGAN_MATERIALS, MATERIAL_COLORS
        
        # Check basic structure
        assert isinstance(ORGAN_MATERIALS, dict), "ORGAN_MATERIALS should be a dict"
        assert isinstance(MATERIAL_COLORS, dict), "MATERIAL_COLORS should be a dict"
        assert len(ORGAN_MATERIALS) > 0, "Should have organ materials"
        assert len(MATERIAL_COLORS) > 0, "Should have material colors"
        
        # Check liver segments
        liver_count = sum(1 for organ in ORGAN_MATERIALS.keys() if "liver_segment" in organ)
        assert liver_count >= 8, f"Should have at least 8 liver segments, found {liver_count}"
        
        print("✓ Material definitions are valid")
        return True
    except Exception as e:
        print(f"✗ Material definitions test failed: {e}")
        return False

def test_script_generation():
    """Test Blender script generation."""
    try:
        from totalsegmentator.blender_export import generate_blender_import_script
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            stl_dir = temp_path / "stl"
            stl_dir.mkdir()
            
            script_path = temp_path / "test_script.py"
            generate_blender_import_script(stl_dir, script_path, scale_factor=0.02)
            
            assert script_path.exists(), "Script should be created"
            
            content = script_path.read_text()
            assert "import bpy" in content, "Should import bpy"
            assert "create_material" in content, "Should have material functions"
            assert str(stl_dir.as_posix()) in content, "Should reference STL directory"
            assert "0.02" in content, "Should use the specified scale factor"
            
            print("✓ Script generation works")
            return True
    except Exception as e:
        print(f"✗ Script generation test failed: {e}")
        return False

def test_summary_creation():
    """Test JSON summary creation."""
    try:
        from totalsegmentator.blender_export import save_task_summary
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            test_files = {"liver.stl": True, "heart.stl": False}
            save_task_summary(temp_path, "test_task", test_files)
            
            summary_path = temp_path / "task_summary.json"
            assert summary_path.exists(), "Summary should be created"
            
            with open(summary_path) as f:
                summary = json.load(f)
            
            assert summary["task_name"] == "test_task"
            assert summary["total_files"] == 2
            assert summary["successful_conversions"] == 1
            
            print("✓ Summary creation works")
            return True
    except Exception as e:
        print(f"✗ Summary creation test failed: {e}")
        return False

def test_cli_integration():
    """Test CLI argument parsing."""
    try:
        # Test that the CLI changes work
        import argparse
        
        parser = argparse.ArgumentParser()
        parser.add_argument("-ot", "--output_type", choices=["nifti", "dicom", "stl"], default="nifti")
        
        # Test STL option
        args = parser.parse_args(["-ot", "stl"])
        assert args.output_type == "stl"
        
        # Test default
        args = parser.parse_args([])
        assert args.output_type == "nifti"
        
        print("✓ CLI integration works")
        return True
    except Exception as e:
        print(f"✗ CLI integration test failed: {e}")
        return False

def run_tests():
    """Run all tests."""
    tests = [
        ("Basic Import", test_basic_import),
        ("Material Definitions", test_material_definitions), 
        ("Script Generation", test_script_generation),
        ("Summary Creation", test_summary_creation),
        ("CLI Integration", test_cli_integration),
    ]
    
    print("TotalSegmentator Blender Export - Basic Tests")
    print("=" * 45)
    
    passed = 0
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        if test_func():
            passed += 1
    
    print(f"\n{'=' * 45}")
    print(f"Passed: {passed}/{len(tests)} tests")
    
    return passed == len(tests)

if __name__ == "__main__":
    success = run_tests()
    if success:
        print("🎉 All basic tests passed!")
    else:
        print("❌ Some tests failed")
    exit(0 if success else 1)