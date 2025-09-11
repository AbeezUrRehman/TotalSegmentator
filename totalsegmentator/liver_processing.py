"""
Specialized processing for liver segmentation tasks.
Handles the specific directory structure mentioned in the problem statement.
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Union

from totalsegmentator.blender_export import export_segmentations_to_stl, save_task_summary


def process_liver_segmentation_results(results_dir: Union[str, Path], 
                                     output_format: str = "stl",
                                     generate_blender_scripts: bool = True) -> None:
    """
    Process liver segmentation results in the specific directory structure:
    
    results/
    ├── liver_segments/           # "liver: segments" 
    │   ├── liver_segment_1.nii.gz ... liver_segment_8.nii.gz
    │   └── task_summary.json
    ├── liver_vessels/            # "liver: vessels"
    │   ├── blood_vessel.nii.gz   # (renamed from liver_vessels)
    │   ├── neoplasm.nii.gz       # (renamed from liver_tumor)
    │   └── task_summary.json
    └── total_vessels/            # "total"
        ├── inferior_vena_cava.nii.gz
        ├── portal_vein_and_splenic_vein.nii.gz
        └── task_summary.json
    
    Args:
        results_dir: Path to the results directory
        output_format: Output format ('stl' or 'nifti')
        generate_blender_scripts: Whether to generate Blender import scripts
    """
    results_path = Path(results_dir)
    
    # Process each subdirectory if it exists
    subdirs_to_process = [
        ("liver_segments", "liver segments"),
        ("liver_vessels", "liver vessels"), 
        ("total_vessels", "total vessels")
    ]
    
    for subdir, task_name in subdirs_to_process:
        subdir_path = results_path / subdir
        if subdir_path.exists() and subdir_path.is_dir():
            print(f"Processing {subdir}...")
            process_segmentation_directory(subdir_path, task_name, output_format, generate_blender_scripts)
    
    print("Liver segmentation processing completed!")


def process_segmentation_directory(dir_path: Path, task_name: str, 
                                 output_format: str = "stl",
                                 generate_blender_scripts: bool = True) -> None:
    """
    Process a single segmentation directory.
    
    Args:
        dir_path: Path to the segmentation directory
        task_name: Name of the task for summary
        output_format: Output format ('stl' or 'nifti')
        generate_blender_scripts: Whether to generate Blender import scripts
    """
    
    if output_format.lower() == "stl":
        # Create STL output directory
        stl_dir = dir_path / "stl"
        
        # Export segmentations to STL
        results = export_segmentations_to_stl(
            input_dir=dir_path,
            output_dir=stl_dir,
            file_pattern="*.nii.gz",
            generate_blender_script=generate_blender_scripts,
            smoothing=10,
            reduction=0.9
        )
        
        # Save task summary
        save_task_summary(stl_dir, task_name, results)
        
        print(f"  Converted {sum(results.values())}/{len(results)} files to STL format")
        
        if generate_blender_scripts:
            blender_script = stl_dir / "import_organs_blender.py"
            if blender_script.exists():
                print(f"  Generated Blender import script: {blender_script}")
    
    else:
        print(f"  Directory {dir_path} already contains NIfTI files")


def create_specialized_liver_scripts(output_dir: Union[str, Path]) -> None:
    """
    Create specialized Blender scripts for liver visualization with proper color coding.
    """
    output_path = Path(output_dir)
    
    # Create a specialized liver visualization script
    liver_script = f'''import bpy
import os

# Specialized script for liver segmentation visualization
# Based on TotalSegmentator liver processing

def setup_liver_materials():
    """Setup materials specifically for liver visualization"""
    materials = {{}}
    
    # Liver segment materials (different shades of liver color)
    liver_base_color = (0.359082, 0.052501, 0.044477, 1.0)
    for i in range(1, 9):
        intensity_factor = 0.8 + (i * 0.03)  # Vary intensity
        color = (
            min(1.0, liver_base_color[0] * intensity_factor),
            min(1.0, liver_base_color[1] * intensity_factor), 
            min(1.0, liver_base_color[2] * intensity_factor),
            1.0
        )
        materials[f"LiverSegment{{i}}"] = create_material(f"LiverSegment{{i}}", color)
    
    # Vessel materials
    materials["BloodVessel"] = create_material("BloodVessel", (0.675526, 0.020398, 0.041993, 1.0))  # Artery red
    materials["Neoplasm"] = create_material("Neoplasm", (0.8, 0.1, 0.1, 1.0))  # Bright red for tumors
    materials["InferiorVenaCava"] = create_material("InferiorVenaCava", (0.071473, 0.01412, 0.37347, 1.0))  # Vein blue
    materials["PortalVein"] = create_material("PortalVein", (0.047439, 0.046528, 0.434352, 1.0))  # Portal blue
    
    return materials

def create_material(name, color):
    """Create a material with specified name and color"""
    if name in bpy.data.materials:
        bpy.data.materials.remove(bpy.data.materials[name])
    
    material = bpy.data.materials.new(name=name)
    material.use_nodes = True
    
    nodes = material.node_tree.nodes
    principled = nodes.get("Principled BSDF")
    
    if principled:
        principled.inputs['Base Color'].default_value = color
        # Add some transparency for better visualization
        principled.inputs['Alpha'].default_value = 0.85
        material.blend_method = 'BLEND'
    
    return material

def apply_liver_materials():
    """Apply appropriate materials to liver objects"""
    materials = setup_liver_materials()
    
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH':
            obj_name = obj.name.lower()
            
            # Apply materials based on object name
            if "liver_segment" in obj_name:
                segment_num = obj_name.split("_")[-1]
                material_name = f"LiverSegment{{segment_num}}"
                if material_name in materials:
                    apply_material_to_object(obj.name, material_name)
            elif "blood_vessel" in obj_name:
                apply_material_to_object(obj.name, "BloodVessel")
            elif "neoplasm" in obj_name:
                apply_material_to_object(obj.name, "Neoplasm")
            elif "inferior_vena_cava" in obj_name:
                apply_material_to_object(obj.name, "InferiorVenaCava")
            elif "portal_vein" in obj_name:
                apply_material_to_object(obj.name, "PortalVein")

def apply_material_to_object(object_name, material_name):
    """Apply material to specified object"""
    obj = bpy.data.objects.get(object_name)
    material = bpy.data.materials.get(material_name)
    
    if not obj or not material:
        return False
    
    if obj.data.materials:
        obj.data.materials[0] = material
    else:
        obj.data.materials.append(material)
    
    return True

def setup_liver_collections():
    """Organize liver objects into logical collections"""
    
    collections = {{
        "LiverSegments": bpy.data.collections.new("Liver Segments"),
        "LiverVessels": bpy.data.collections.new("Liver Vessels"),
        "TotalVessels": bpy.data.collections.new("Total Vessels"),
    }}
    
    for collection in collections.values():
        bpy.context.scene.collection.children.link(collection)
    
    # Move objects to appropriate collections
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH':
            obj_name = obj.name.lower()
            moved = False
            
            if "liver_segment" in obj_name:
                collections["LiverSegments"].objects.link(obj)
                moved = True
            elif any(vessel in obj_name for vessel in ["blood_vessel", "neoplasm"]):
                collections["LiverVessels"].objects.link(obj)
                moved = True
            elif any(vessel in obj_name for vessel in ["inferior_vena_cava", "portal_vein"]):
                collections["TotalVessels"].objects.link(obj)
                moved = True
            
            # Remove from default collection if moved
            if moved and obj.name in bpy.context.scene.collection.objects:
                bpy.context.scene.collection.objects.unlink(obj)

def import_and_setup_liver_stls(folder_path):
    """Import STL files and set up liver visualization"""
    
    # Import all STL files
    if not os.path.exists(folder_path):
        print(f"Error: Folder {{folder_path}} does not exist")
        return
    
    stl_files = [f for f in os.listdir(folder_path) if f.endswith('.stl')]
    
    if not stl_files:
        print(f"No STL files found in {{folder_path}}")
        return
    
    # Import each STL file
    for stl_file in stl_files:
        file_path = os.path.join(folder_path, stl_file)
        obj_name = os.path.splitext(stl_file)[0]
        
        # Import STL
        bpy.ops.import_mesh.stl(filepath=file_path)
        
        # Get the imported object and rename it
        if bpy.context.selected_objects:
            obj = bpy.context.selected_objects[0]
            obj.name = obj_name
            
            # Scale and position (adjust as needed)
            obj.scale = (0.02, 0.02, 0.02)
            obj.rotation_euler[0] = -1.5708  # Rotate around X-axis
    
    # Apply materials and organize collections
    apply_liver_materials()
    setup_liver_collections()
    
    print(f"Successfully imported and set up {{len(stl_files)}} liver objects")

# Usage example:
# Change this path to your STL directory
# folder_path = r"/path/to/your/stl/files"
# import_and_setup_liver_stls(folder_path)

print("Liver visualization script loaded. Call import_and_setup_liver_stls(folder_path) to import your STL files.")
'''
    
    script_path = output_path / "liver_visualization_blender.py"
    with open(script_path, 'w') as f:
        f.write(liver_script)
    
    print(f"Created specialized liver visualization script: {script_path}")


if __name__ == "__main__":
    # Example usage
    import sys
    if len(sys.argv) > 1:
        results_dir = sys.argv[1]
        output_format = sys.argv[2] if len(sys.argv) > 2 else "stl"
        process_liver_segmentation_results(results_dir, output_format)
    else:
        print("Usage: python liver_processing.py <results_directory> [output_format]")
        print("Example: python liver_processing.py /path/to/results stl")