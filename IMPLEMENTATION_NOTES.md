# TotalSegmentator Blender Export Enhancement

## Overview

This enhancement adds comprehensive STL export and Blender integration capabilities to TotalSegmentator, specifically addressing the need for improved 3D visualization of liver segmentation results as requested in the issue.

## Key Features

### 1. STL Export Support
- **New output format**: Added `--output_type stl` option to CLI
- **VTK-based conversion**: High-quality mesh generation from segmentation masks
- **Optimized for 3D software**: Compatible with Blender, 3D Slicer, and other 3D applications
- **Configurable quality**: Adjustable mesh smoothing and reduction parameters

### 2. Blender Integration
- **Automatic script generation**: Creates ready-to-use Blender import scripts
- **Material system**: Pre-defined anatomical colors based on @tk1971-Jpn/Import-organ-STL-data-into-Blender
- **Organized collections**: Automatically groups organs by type (bones, vessels, muscles, etc.)
- **Proper scaling**: Objects imported at appropriate size for Blender workspace

### 3. Specialized Liver Processing
- **Directory structure support**: Handles the specific liver results structure mentioned in the issue:
  ```
  results/
  ├── liver_segments/     # liver segments 1-8
  ├── liver_vessels/      # blood vessels, neoplasms
  └── total_vessels/      # IVC, portal vein
  ```
- **Dedicated CLI tool**: `totalseg_process_liver` command for batch processing
- **Enhanced visualization**: Specialized Blender scripts for liver structures

## Installation

```bash
# Install with STL/Blender support
pip install TotalSegmentator[blender]

# Or install VTK separately
pip install TotalSegmentator vtk
```

## Usage Examples

### Basic STL Export
```bash
# Export any segmentation task as STL
TotalSegmentator -i input.nii.gz -o output_dir -ot stl

# Export liver segments specifically
TotalSegmentator -i input.nii.gz -o liver_segments -ot stl --task liver_segments

# Export liver vessels
TotalSegmentator -i input.nii.gz -o liver_vessels -ot stl --task liver_vessels
```

### Liver Results Processing
```bash
# Process complete liver results directory
totalseg_process_liver -i results_directory -f stl

# Keep NIfTI but generate Blender scripts
totalseg_process_liver -i results_directory -f nifti
```

### Python API
```python
from totalsegmentator import totalsegmentator
from totalsegmentator.liver_processing import process_liver_segmentation_results

# STL export via API
totalsegmentator(
    input="scan.nii.gz",
    output="output_dir", 
    output_type="stl",
    task="liver_segments"
)

# Process liver results
process_liver_segmentation_results(
    results_dir="liver_results",
    output_format="stl",
    generate_blender_scripts=True
)
```

## Output Structure

STL export creates the following structure:
```
output_directory/
├── organ1.stl                    # Individual organ STL files
├── organ2.stl
├── ...
├── import_organs_blender.py      # Blender import script
├── liver_visualization_blender.py # Specialized liver script
└── task_summary.json            # Conversion summary
```

## Blender Workflow

1. **Enable STL Import**: In Blender Preferences → Add-ons → Enable "Import-Export STL files"
2. **Open Scripting Workspace**: Switch to Scripting tab in Blender
3. **Load Script**: Open the generated `import_organs_blender.py`
4. **Set Path**: Update `folder_path` variable to your STL directory
5. **Run Script**: Execute to import all organs with proper materials and organization

### Liver-Specific Workflow

For liver segmentations, use the specialized `liver_visualization_blender.py` script which provides:
- Individual colors for each liver segment (8 segments)
- Distinct materials for vessels and neoplasms
- Organized collections: "Liver Segments", "Liver Vessels", "Total Vessels"
- Semi-transparent materials for better internal visualization

## Technical Implementation

### Files Modified/Added

1. **Core Integration**:
   - `totalsegmentator/nnunet.py`: Added STL output handling
   - `totalsegmentator/bin/TotalSegmentator.py`: Added STL CLI option
   - `setup.py`: Added VTK dependency and new CLI command

2. **New Modules**:
   - `totalsegmentator/blender_export.py`: STL conversion and Blender script generation
   - `totalsegmentator/liver_processing.py`: Specialized liver processing
   - `totalsegmentator/bin/totalseg_process_liver.py`: Liver CLI tool

3. **Tests and Documentation**:
   - `tests/test_basic_blender.py`: Basic functionality tests
   - `BLENDER_EXPORT.md`: Comprehensive documentation

### Architecture Decisions

1. **Conditional Dependencies**: VTK is optional - functionality gracefully degrades if not available
2. **Backwards Compatibility**: All existing workflows continue to work unchanged
3. **Modular Design**: Blender functionality is separated into dedicated modules
4. **Error Handling**: Fallback to NIfTI if STL conversion fails

## Material System

Based on @tk1971-Jpn/Import-organ-STL-data-into-Blender color scheme:

- **Bones**: Light brown (`#827259`)
- **Muscles**: Dark red (`#751D19`)
- **Liver**: Dark red-brown (`#5C0D0B`) with variations for segments
- **Arteries**: Bright red (`#AC0510`)
- **Veins**: Blue (`#125F60`)
- **Organs**: Specific colors for heart, lungs, kidneys, etc.

## Benefits for 3D Slicer Users

- **STL format** is natively supported by 3D Slicer
- **Better performance** compared to loading large NIfTI files
- **Mesh-based visualization** allows for advanced rendering techniques
- **Smaller file sizes** due to mesh optimization
- **Cross-platform compatibility** with medical visualization software

## Testing

Comprehensive test suite covers:
- Basic import functionality
- Material definition validation  
- Blender script generation
- CLI argument parsing
- JSON summary creation

Run tests with:
```bash
cd TotalSegmentator
python tests/test_basic_blender.py
```

## Dependencies

- **VTK**: For STL generation (optional, installed with `pip install vtk`)
- **nibabel**: For NIfTI processing (already included)
- **numpy**: For data handling (already included)

## Performance Considerations

- **Memory efficient**: Processes one organ at a time
- **Configurable quality**: Balance between file size and detail
- **Multi-threaded**: Leverages existing TotalSegmentator threading
- **Fallback handling**: Automatic fallback to NIfTI if STL conversion fails

## Future Enhancements

Potential improvements identified during development:
- Direct Blender add-on for seamless integration
- Additional output formats (OBJ, PLY)
- Advanced material properties (transparency, reflectance)
- Batch processing for multiple scans
- Integration with 3D Slicer scripting

## Credits

- Incorporates techniques from @tk1971-Jpn/Import-organ-STL-data-into-Blender
- VTK mesh processing algorithms
- TotalSegmentator framework by Jakob Wasserthal