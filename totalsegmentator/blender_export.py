"""
Blender export functionality for TotalSegmentator.
Includes STL export and Blender import script generation.

Based on techniques from @tk1971-Jpn/Import-organ-STL-data-into-Blender
"""

import os
from pathlib import Path
from typing import Dict, Union, List, Tuple
import json

# Conditional imports - these will be checked at runtime
NIBABEL_AVAILABLE = False
VTK_AVAILABLE = False

try:
    import nibabel as nib
    NIBABEL_AVAILABLE = True
except ImportError:
    nib = None

try:
    import vtk
    from vtk.util import numpy_support
    VTK_AVAILABLE = True
except ImportError:
    vtk = None
    numpy_support = None

# numpy will be imported when needed
np = None


# Color and material definitions based on tk1971-Jpn's repository
ORGAN_MATERIALS = {
    # Bone structures
    "skull": ("Bone", (0.509338, 0.448805, 0.390992, 1.0)),
    "costal_cartilage": ("Bone", (0.509338, 0.448805, 0.390992, 1.0)),
    "sternum": ("Bone", (0.509338, 0.448805, 0.390992, 1.0)),
    "left_clavicle": ("Bone", (0.509338, 0.448805, 0.390992, 1.0)),
    "right_clavicle": ("Bone", (0.509338, 0.448805, 0.390992, 1.0)),
    "left_scapula": ("Bone", (0.509338, 0.448805, 0.390992, 1.0)),
    "right_scapula": ("Bone", (0.509338, 0.448805, 0.390992, 1.0)),
    "left_humerus": ("Bone", (0.509338, 0.448805, 0.390992, 1.0)),
    "right_humerus": ("Bone", (0.509338, 0.448805, 0.390992, 1.0)),
    "spinal_cord": ("Bone", (0.509338, 0.448805, 0.390992, 1.0)),
    
    # Muscles
    "left_iliopsoas_muscle": ("Muscle", (0.458575, 0.114023, 0.099804, 1.0)),
    "right_iliopsoas_muscle": ("Muscle", (0.458575, 0.114023, 0.099804, 1.0)),
    
    # Organs
    "liver": ("Liver", (0.359082, 0.052501, 0.044477, 1.0)),
    "stomach": ("Stomach", (0.483567, 0.277414, 0.269021, 1.0)),
    "heart": ("Heart", (0.675526, 0.020398, 0.041993, 1.0)),
    "left_kidney": ("Kidney", (0.359082, 0.084555, 0.06085, 1.0)),
    "right_kidney": ("Kidney", (0.359082, 0.084555, 0.06085, 1.0)),
    "pancreas": ("Pancreas", (0.450415, 0.259994, 0.102502, 1.0)),
    "gallbladder": ("GB", (0.12796, 0.16291, 0.069646, 1.0)),
    "spleen": ("Spleen", (0.110568, 0.021969, 0.025012, 1.0)),
    "urinary_bladder": ("Bladder", (0.591379, 0.383078, 0.371987, 1.0)),
    "prostate": ("Prostate", (0.366235, 0.160072, 0.063098, 1.0)),
    
    # Vessels
    "aorta": ("Artery", (0.675526, 0.020398, 0.041993, 1.0)),
    "superior_vena_cava": ("Vein", (0.071473, 0.01412, 0.37347, 1.0)),
    "inferior_vena_cava": ("Vein", (0.071473, 0.01412, 0.37347, 1.0)),
    "portal_vein_and_splenic_vein": ("Portal", (0.047439, 0.046528, 0.434352, 1.0)),
    
    # Lung
    "superior_lobe_of_right_lung": ("Lung", (0.475151, 0.316953, 0.299059, 1.0)),
    "inferior_lobe_of_left_lung": ("Lung", (0.475151, 0.316953, 0.299059, 1.0)),
    "inferior_lobe_of_right_lung": ("Lung", (0.475151, 0.316953, 0.299059, 1.0)),
    "middle_lobe_of_right_lung": ("Lung", (0.475151, 0.316953, 0.299059, 1.0)),
    "superior_lobe_of_left_lung": ("Lung", (0.475151, 0.316953, 0.299059, 1.0)),
    
    # Liver segments - use liver color variations
    "liver_segment_1": ("Liver", (0.359082, 0.052501, 0.044477, 1.0)),
    "liver_segment_2": ("Liver", (0.4, 0.06, 0.05, 1.0)),
    "liver_segment_3": ("Liver", (0.42, 0.065, 0.055, 1.0)),
    "liver_segment_4": ("Liver", (0.44, 0.07, 0.06, 1.0)),
    "liver_segment_5": ("Liver", (0.46, 0.075, 0.065, 1.0)),
    "liver_segment_6": ("Liver", (0.48, 0.08, 0.07, 1.0)),
    "liver_segment_7": ("Liver", (0.5, 0.085, 0.075, 1.0)),
    "liver_segment_8": ("Liver", (0.52, 0.09, 0.08, 1.0)),
    
    # Liver vessels
    "blood_vessel": ("Artery", (0.675526, 0.020398, 0.041993, 1.0)),
    "neoplasm": ("Liver", (0.8, 0.1, 0.1, 1.0)),  # Distinct color for tumors
}

# Material type definitions
MATERIAL_COLORS = {
    "Bone": (0.509338, 0.448805, 0.390992, 1.0),
    "Muscle": (0.458575, 0.114023, 0.099804, 1.0),
    "Liver": (0.359082, 0.052501, 0.044477, 1.0),
    "Stomach": (0.483567, 0.277414, 0.269021, 1.0),
    "Artery": (0.675526, 0.020398, 0.041993, 1.0),
    "Vein": (0.071473, 0.01412, 0.37347, 1.0),
    "Kidney": (0.359082, 0.084555, 0.06085, 1.0),
    "Adrenal": (0.799999, 0.254006, 0.03054, 1.0),
    "Pancreas": (0.450415, 0.259994, 0.102502, 1.0),
    "GB": (0.12796, 0.16291, 0.069646, 1.0),
    "Heart": (0.675526, 0.020398, 0.041993, 1.0),
    "Portal": (0.047439, 0.046528, 0.434352, 1.0),
    "Lung": (0.475151, 0.316953, 0.299059, 1.0),
    "Thyroid": (0.37347, 0.24654, 0.067987, 1.0),
    "Bladder": (0.591379, 0.383078, 0.371987, 1.0),
    "Spleen": (0.110568, 0.021969, 0.025012, 1.0),
    "Prostate": (0.366235, 0.160072, 0.063098, 1.0),
    "Colon": (0.403241, 0.212665, 0.103747, 1.0),
}


def check_dependencies():
    """Check if required dependencies are available."""
    if not VTK_AVAILABLE:
        raise ImportError("VTK is required for STL export. Please install with: pip install vtk")
    if not NIBABEL_AVAILABLE:
        raise ImportError("nibabel is required for NIfTI processing. Please install with: pip install nibabel")
    
    # Import numpy when needed
    global np
    if np is None:
        try:
            import numpy as np_module
            np = np_module
        except ImportError:
            raise ImportError("numpy is required for data processing. Please install with: pip install numpy")


def nifti_to_stl(nifti_path: Union[str, Path], output_path: Union[str, Path], 
                 smoothing: int = 10, reduction: float = 0.9) -> bool:
    """
    Convert a NIfTI segmentation file to STL format.
    
    Args:
        nifti_path: Path to input NIfTI file
        output_path: Path for output STL file
        smoothing: Number of smoothing iterations (0 = no smoothing)
        reduction: Mesh reduction factor (0.0-1.0, where 1.0 = no reduction)
    
    Returns:
        bool: True if successful, False otherwise
    """
    check_dependencies()
    
    try:
        # Load NIfTI file
        nifti_img = nib.load(str(nifti_path))
        data = nifti_img.get_fdata()
        
        # Create VTK image data
        vtk_data = vtk.vtkImageData()
        vtk_data.SetDimensions(data.shape)
        vtk_data.SetSpacing(1.0, 1.0, 1.0)
        vtk_data.SetOrigin(0.0, 0.0, 0.0)
        
        # Convert numpy array to VTK array
        vtk_array = numpy_support.numpy_to_vtk(data.ravel(), deep=True, array_type=vtk.VTK_FLOAT)
        vtk_data.GetPointData().SetScalars(vtk_array)
        
        # Generate mesh using marching cubes
        marching_cubes = vtk.vtkMarchingCubes()
        marching_cubes.SetInputData(vtk_data)
        marching_cubes.SetValue(0, 0.5)  # Threshold for binary segmentation
        marching_cubes.Update()
        
        mesh = marching_cubes.GetOutput()
        
        # Apply smoothing if requested
        if smoothing > 0:
            smoother = vtk.vtkSmoothPolyDataFilter()
            smoother.SetInputData(mesh)
            smoother.SetNumberOfIterations(smoothing)
            smoother.SetRelaxationFactor(0.1)
            smoother.Update()
            mesh = smoother.GetOutput()
        
        # Apply mesh reduction if requested
        if reduction < 1.0:
            decimate = vtk.vtkDecimatePro()
            decimate.SetInputData(mesh)
            decimate.SetTargetReduction(1.0 - reduction)
            decimate.Update()
            mesh = decimate.GetOutput()
        
        # Write STL file
        stl_writer = vtk.vtkSTLWriter()
        stl_writer.SetFileName(str(output_path))
        stl_writer.SetInputData(mesh)
        stl_writer.Write()
        
        return True
        
    except Exception as e:
        print(f"Error converting {nifti_path} to STL: {e}")
        return False


def generate_blender_import_script(stl_directory: Union[str, Path], 
                                 output_script_path: Union[str, Path],
                                 scale_factor: float = 0.02) -> None:
    """
    Generate a Blender Python script to import STL files with proper materials and positioning.
    
    Args:
        stl_directory: Directory containing STL files
        output_script_path: Path for output Blender script
        scale_factor: Scale factor for imported objects (default: 0.02 as in original)
    """
    stl_dir = Path(stl_directory)
    
    script_content = f'''import bpy
import os

# Directory path and initial offsets
folder_path = r'{stl_dir.as_posix()}'
x_move = 0
y_move = 7.5
z_move = 0
scale_factor = {scale_factor}

# Material and color definitions
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
    
    return material

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

# Create materials
'''

    # Add material creation code
    for material_name, color in MATERIAL_COLORS.items():
        script_content += f'{material_name.lower()} = create_material("{material_name}", {color})\n'
    
    script_content += '''
# Get a list of STL file paths
file_paths = [
    os.path.join(folder_path, filename)
    for filename in os.listdir(folder_path)
    if os.path.isfile(os.path.join(folder_path, filename)) and filename.endswith('.stl')
]

# Import STL files one by one
for file_path in file_paths:
    # Extract the file name and object name
    name = os.path.basename(file_path)
    obj_name = os.path.splitext(name)[0]

    # Import the STL file
    bpy.ops.import_mesh.stl(filepath=file_path)

    # Get the imported object
    obj = bpy.context.selected_objects[0]
    obj.name = obj_name

    # Resize the object
    obj.scale = (scale_factor, scale_factor, scale_factor)

    # Adjust rotation and position
    obj.rotation_euler[0] = -1.5708  # Rotate around the X-axis
    obj.location = (x_move, y_move, z_move)

# Apply materials to objects based on organ names
'''

    # Add material assignment code
    for organ_name, (material_type, _) in ORGAN_MATERIALS.items():
        script_content += f'apply_material_to_object("{organ_name}", "{material_type}")\n'
    
    script_content += '''
# Create collections for organization (optional)
def create_collection_if_not_exists(name):
    if name not in bpy.data.collections:
        collection = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(collection)
        return collection
    return bpy.data.collections[name]

# Organize objects into collections by type
collections = {
    "Bones": create_collection_if_not_exists("Bones"),
    "Organs": create_collection_if_not_exists("Organs"), 
    "Vessels": create_collection_if_not_exists("Vessels"),
    "Muscles": create_collection_if_not_exists("Muscles"),
    "Liver": create_collection_if_not_exists("Liver"),
}

# Move objects to appropriate collections
for obj in bpy.context.scene.objects:
    if obj.type == 'MESH':
        obj_name = obj.name.lower()
        moved = False
        
        if "liver" in obj_name:
            collections["Liver"].objects.link(obj)
            moved = True
        elif any(bone in obj_name for bone in ["skull", "rib", "vertebra", "femur", "humerus", "clavicle"]):
            collections["Bones"].objects.link(obj)
            moved = True
        elif any(vessel in obj_name for vessel in ["aorta", "vena", "artery", "vein", "portal"]):
            collections["Vessels"].objects.link(obj)
            moved = True
        elif "muscle" in obj_name:
            collections["Muscles"].objects.link(obj)
            moved = True
        elif any(organ in obj_name for organ in ["heart", "lung", "kidney", "liver", "stomach", "spleen"]):
            collections["Organs"].objects.link(obj)
            moved = True
        
        # Remove from default collection if moved to a specific one
        if moved and obj.name in bpy.context.scene.collection.objects:
            bpy.context.scene.collection.objects.unlink(obj)

print("Import completed successfully!")
'''

    # Write script to file
    with open(output_script_path, 'w') as f:
        f.write(script_content)


def export_segmentations_to_stl(input_dir: Union[str, Path], output_dir: Union[str, Path],
                               file_pattern: str = "*.nii.gz", 
                               generate_blender_script: bool = True,
                               smoothing: int = 10, reduction: float = 0.9) -> Dict[str, bool]:
    """
    Export all segmentation files in a directory to STL format.
    
    Args:
        input_dir: Directory containing NIfTI segmentation files
        output_dir: Directory for STL output files
        file_pattern: Pattern to match input files
        generate_blender_script: Whether to generate Blender import script
        smoothing: Smoothing iterations for STL generation
        reduction: Mesh reduction factor
    
    Returns:
        Dict mapping file names to success status
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    results = {}
    
    # Find all matching files
    nifti_files = list(input_path.glob(file_pattern))
    
    for nifti_file in nifti_files:
        stl_file = output_path / f"{nifti_file.stem.replace('.nii', '')}.stl"
        success = nifti_to_stl(nifti_file, stl_file, smoothing=smoothing, reduction=reduction)
        results[nifti_file.name] = success
        
        if success:
            print(f"Successfully converted {nifti_file.name} to STL")
        else:
            print(f"Failed to convert {nifti_file.name} to STL")
    
    # Generate Blender import script
    if generate_blender_script and results:
        script_path = output_path / "import_organs_blender.py"
        generate_blender_import_script(output_path, script_path)
        print(f"Generated Blender import script: {script_path}")
    
    return results


def save_task_summary(output_dir: Union[str, Path], task_name: str, 
                     converted_files: Dict[str, bool]) -> None:
    """
    Save a summary JSON file for the conversion task.
    
    Args:
        output_dir: Output directory
        task_name: Name of the segmentation task
        converted_files: Dictionary of file conversion results
    """
    summary = {
        "task_name": task_name,
        "output_format": "STL",
        "total_files": len(converted_files),
        "successful_conversions": sum(converted_files.values()),
        "failed_conversions": len(converted_files) - sum(converted_files.values()),
        "files": converted_files,
        "blender_compatible": True,
        "slicer_3d_compatible": True
    }
    
    summary_path = Path(output_dir) / "task_summary.json"
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)