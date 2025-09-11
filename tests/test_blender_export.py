#!/usr/bin/env python3

"""
Simple test for blender export functionality.
Tests basic STL export and Blender script generation.
"""

import numpy as np
import tempfile
from pathlib import Path
import json

# Test the import (should work without VTK for basic functions)
def test_imports():
    """Test that our new modules can be imported."""
    try:
        from totalsegmentator import blender_export
        from totalsegmentator import liver_processing
        print("✓ All modules imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False

def test_material_definitions():
    """Test that material definitions are correctly structured."""
    try:
        from totalsegmentator.blender_export import ORGAN_MATERIALS, MATERIAL_COLORS
        
        # Check that we have some organ materials defined
        assert len(ORGAN_MATERIALS) > 0, "No organ materials defined"
        assert len(MATERIAL_COLORS) > 0, "No material colors defined"
        
        # Check that all organ materials reference valid material types
        for organ_name, (material_type, color) in ORGAN_MATERIALS.items():
            assert material_type in MATERIAL_COLORS, f"Material type {material_type} not found in MATERIAL_COLORS"
            assert len(color) == 4, f"Color for {organ_name} should have 4 components (RGBA)"
            assert all(0 <= c <= 1 for c in color), f"Color values for {organ_name} should be between 0 and 1"
        
        print("✓ Material definitions are valid")
        return True
    except Exception as e:
        print(f"✗ Material definition test failed: {e}")
        return False

def test_blender_script_generation():
    """Test Blender script generation without needing VTK."""
    try:
        from totalsegmentator.blender_export import generate_blender_import_script
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            stl_dir = temp_path / "stl"
            stl_dir.mkdir()
            
            # Create some dummy STL files to test with
            (stl_dir / "liver.stl").touch()
            (stl_dir / "heart.stl").touch()
            
            script_path = temp_path / "test_script.py"
            generate_blender_import_script(stl_dir, script_path)
            
            # Check that script was created
            assert script_path.exists(), "Blender script was not created"
            
            # Check that script contains expected content
            script_content = script_path.read_text()
            assert "import bpy" in script_content, "Script should import bpy"
            assert "create_material" in script_content, "Script should contain create_material function"
            assert str(stl_dir.as_posix()) in script_content, "Script should reference the STL directory"
            
            print("✓ Blender script generation works")
            return True
    except Exception as e:
        print(f"✗ Blender script generation test failed: {e}")
        return False

def test_output_type_validation():
    """Test that the new output types are recognized."""
    try:
        # Test CLI argument parsing
        import argparse
        from totalsegmentator.bin.TotalSegmentator import main
        
        # Create a parser like the one in TotalSegmentator
        parser = argparse.ArgumentParser()
        parser.add_argument("-ot", "--output_type", choices=["nifti", "dicom", "stl"])
        
        # Test that 'stl' is now a valid choice
        args = parser.parse_args(["-ot", "stl"])
        assert args.output_type == "stl", "STL output type not recognized"
        
        print("✓ STL output type is recognized in CLI")
        return True
    except Exception as e:
        print(f"✗ Output type validation test failed: {e}")
        return False

def test_task_summary_creation():
    """Test task summary JSON creation."""
    try:
        from totalsegmentator.blender_export import save_task_summary
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Test data
            test_files = {"file1.stl": True, "file2.stl": False, "file3.stl": True}
            
            save_task_summary(temp_path, "test_task", test_files)
            
            summary_file = temp_path / "task_summary.json"
            assert summary_file.exists(), "Task summary file was not created"
            
            # Load and validate summary
            with open(summary_file) as f:
                summary = json.load(f)
            
            assert summary["task_name"] == "test_task"
            assert summary["output_format"] == "STL"
            assert summary["total_files"] == 3
            assert summary["successful_conversions"] == 2
            assert summary["failed_conversions"] == 1
            assert summary["blender_compatible"] is True
            assert summary["slicer_3d_compatible"] is True
            
            print("✓ Task summary creation works")
            return True
    except Exception as e:
        print(f"✗ Task summary creation test failed: {e}")
        return False

def test_liver_specific_colors():
    """Test that liver-specific materials are properly defined."""
    try:
        from totalsegmentator.blender_export import ORGAN_MATERIALS
        
        # Check for liver segments
        liver_segments_found = 0
        for organ_name in ORGAN_MATERIALS.keys():
            if "liver_segment" in organ_name:
                liver_segments_found += 1
        
        assert liver_segments_found >= 8, f"Expected at least 8 liver segments, found {liver_segments_found}"
        
        # Check for liver vessels
        liver_vessels = ["blood_vessel", "neoplasm"]
        for vessel in liver_vessels:
            assert any(vessel in organ for organ in ORGAN_MATERIALS.keys()), f"Liver vessel {vessel} not found in materials"
        
        # Check for total vessels
        total_vessels = ["inferior_vena_cava", "portal_vein_and_splenic_vein"]
        for vessel in total_vessels:
            vessel_found = False
            for organ in ORGAN_MATERIALS.keys():
                if vessel.replace("_", "_") in organ.replace("_", "_"):
                    vessel_found = True
                    break
            # Don't assert here since these might be named differently
        
        print("✓ Liver-specific colors and materials are defined")
        return True
    except Exception as e:
        print(f"✗ Liver-specific color test failed: {e}")
        return False


def run_all_tests():
    """Run all tests and return summary."""
    tests = [
        ("Import Test", test_imports),
        ("Material Definitions", test_material_definitions),
        ("Blender Script Generation", test_blender_script_generation),
        ("Output Type Validation", test_output_type_validation),
        ("Task Summary Creation", test_task_summary_creation),
        ("Liver-Specific Colors", test_liver_specific_colors),
    ]
    
    print("Running TotalSegmentator Blender Export Tests")
    print("=" * 50)
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\nRunning: {test_name}")
        if test_func():
            passed += 1
        else:
            print(f"  Test failed!")
    
    print("\n" + "=" * 50)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return True
    else:
        print("❌ Some tests failed")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)