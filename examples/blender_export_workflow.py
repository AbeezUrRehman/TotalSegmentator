#!/usr/bin/env python3
"""
Example workflow demonstrating the new Blender export functionality.
This script shows how to use the enhanced TotalSegmentator with STL export.
"""

import os
import tempfile
from pathlib import Path

def example_workflow():
    """
    Demonstrate the complete workflow for liver segmentation processing.
    """
    print("TotalSegmentator Blender Export - Example Workflow")
    print("=" * 55)
    
    # This would be your actual workflow:
    print("\n1. LIVER SEGMENTATION WORKFLOW")
    print("   # Process liver segments")
    print("   TotalSegmentator -i liver_scan.nii.gz -o results/liver_segments \\")
    print("                    --task liver_segments -ot stl")
    print()
    print("   # Process liver vessels") 
    print("   TotalSegmentator -i liver_scan.nii.gz -o results/liver_vessels \\")
    print("                    --task liver_vessels -ot stl")
    print()
    print("   # Process total vessels")
    print("   TotalSegmentator -i liver_scan.nii.gz -o results/total_vessels \\")
    print("                    --task total -ot stl --roi_subset inferior_vena_cava portal_vein_and_splenic_vein")
    
    print("\n2. BATCH PROCESSING")
    print("   # Process all liver results at once")
    print("   totalseg_process_liver -i results -f stl")
    
    print("\n3. EXPECTED OUTPUT STRUCTURE")
    print("   results/")
    print("   ├── liver_segments/")
    print("   │   ├── liver_segment_1.stl")
    print("   │   ├── liver_segment_2.stl")
    print("   │   ├── ...")
    print("   │   ├── liver_segment_8.stl")
    print("   │   ├── import_organs_blender.py")
    print("   │   ├── liver_visualization_blender.py") 
    print("   │   └── task_summary.json")
    print("   ├── liver_vessels/")
    print("   │   ├── blood_vessel.stl")
    print("   │   ├── neoplasm.stl") 
    print("   │   ├── import_organs_blender.py")
    print("   │   └── task_summary.json")
    print("   └── total_vessels/")
    print("       ├── inferior_vena_cava.stl")
    print("       ├── portal_vein_and_splenic_vein.stl")
    print("       ├── import_organs_blender.py")
    print("       └── task_summary.json")
    
    print("\n4. BLENDER IMPORT WORKFLOW")
    print("   a) Open Blender")
    print("   b) Enable 'Import-Export STL files' add-on")
    print("   c) Switch to Scripting workspace")
    print("   d) Open 'liver_visualization_blender.py'")
    print("   e) Update folder_path to your STL directory")
    print("   f) Run script to import all organs with proper materials")
    
    print("\n5. 3D SLICER WORKFLOW")
    print("   a) Open 3D Slicer")
    print("   b) Use File → Add Data to import STL files")
    print("   c) Or drag and drop STL files directly")
    print("   d) Models will appear in 3D view with proper names")
    
    print("\n6. PYTHON API EXAMPLE")
    print("""
   # Complete programmatic workflow
   from totalsegmentator import totalsegmentator
   from totalsegmentator.liver_processing import process_liver_segmentation_results
   
   # Run liver segmentation with STL export
   totalsegmentator(
       input="liver_ct.nii.gz",
       output="liver_segments",
       task="liver_segments", 
       output_type="stl"
   )
   
   # Process results directory
   process_liver_segmentation_results(
       results_dir="liver_results",
       output_format="stl",
       generate_blender_scripts=True
   )
   """)
    
    print("\n7. CUSTOMIZATION OPTIONS")
    print("   # Adjust mesh quality")
    print("   TotalSegmentator -i scan.nii.gz -o output -ot stl")
    print("   # Then modify blender_export.py parameters:")
    print("   # - smoothing: Higher = smoother (default: 10)")
    print("   # - reduction: Lower = more detail (default: 0.9)")
    
    print("\n8. TROUBLESHOOTING")
    print("   • VTK not found: pip install vtk")
    print("   • Memory issues: Use --roi_subset to process fewer organs")  
    print("   • Large files: Increase reduction factor in STL generation")
    print("   • Blender import: Ensure STL add-on is enabled")

def demonstrate_materials():
    """Show the available material definitions."""
    try:
        from totalsegmentator.blender_export import ORGAN_MATERIALS, MATERIAL_COLORS
        
        print("\nMATERIAL SYSTEM")
        print("-" * 20)
        print("Available material types:")
        for material, color in MATERIAL_COLORS.items():
            r, g, b, a = [int(c*255) for c in color]
            print(f"  {material:15} RGB({r:3}, {g:3}, {b:3})")
        
        print(f"\nTotal organ mappings: {len(ORGAN_MATERIALS)}")
        print("Liver segments defined:", 
              sum(1 for organ in ORGAN_MATERIALS.keys() if "liver_segment" in organ))
        
    except ImportError:
        print("Import blender_export module to see material definitions")

def check_requirements():
    """Check if requirements for STL export are met."""
    print("\nREQUIREMENTS CHECK")
    print("-" * 20)
    
    # Check Python version
    import sys
    print(f"Python version: {sys.version.split()[0]} {'✓' if sys.version_info >= (3, 9) else '✗'}")
    
    # Check dependencies
    deps = [
        ("nibabel", "pip install nibabel"),
        ("numpy", "pip install numpy"), 
        ("vtk", "pip install vtk"),
    ]
    
    for dep, install_cmd in deps:
        try:
            __import__(dep)
            status = "✓"
        except ImportError:
            status = f"✗ ({install_cmd})"
        print(f"{dep:10}: {status}")

if __name__ == "__main__":
    example_workflow()
    demonstrate_materials()
    check_requirements()
    
    print("\n" + "=" * 55)
    print("For complete documentation, see:")
    print("  • BLENDER_EXPORT.md - User guide") 
    print("  • IMPLEMENTATION_NOTES.md - Technical details")
    print("=" * 55)