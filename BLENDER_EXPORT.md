# Blender Export and STL Generation for TotalSegmentator

This enhancement adds STL export functionality and Blender integration to TotalSegmentator, making it easier to visualize segmentation results in 3D applications like Blender and 3D Slicer.

## Features

### 1. STL Export
- Convert segmentation masks from NIfTI format to STL format
- Optimized for 3D visualization and manipulation
- Configurable mesh smoothing and reduction

### 2. Blender Integration
- Automatic Blender import script generation
- Pre-defined materials and colors for anatomical structures
- Organized collections for different organ systems
- Based on techniques from @tk1971-Jpn/Import-organ-STL-data-into-Blender

### 3. Liver Segmentation Processing
- Specialized handling for liver segmentation results
- Support for the specific directory structure:
  ```
  results/
  ├── liver_segments/
  ├── liver_vessels/
  └── total_vessels/
  ```

## Installation

Install TotalSegmentator with STL export support:

```bash
# Install with Blender/STL support
pip install TotalSegmentator[blender]

# Or install VTK separately
pip install TotalSegmentator vtk
```

## Usage

### Command Line Interface

#### Basic STL Export
```bash
# Export segmentations as STL files
TotalSegmentator -i input.nii.gz -o output_dir -ot stl

# Export only liver segments as STL
TotalSegmentator -i input.nii.gz -o output_dir -ot stl --task liver_segments
```

#### Liver Processing Tool
```bash
# Process liver segmentation results
totalseg_process_liver -i results_directory -f stl

# Keep original NIfTI format but generate Blender scripts
totalseg_process_liver -i results_directory -f nifti
```

### Python API

```python
from totalsegmentator import totalsegmentator

# Export as STL files
totalsegmentator(
    input="input.nii.gz",
    output="output_dir",
    output_type="stl",
    task="liver_segments"
)

# Process liver results directory
from totalsegmentator.liver_processing import process_liver_segmentation_results

process_liver_segmentation_results(
    results_dir="path/to/results",
    output_format="stl",
    generate_blender_scripts=True
)
```

## Output Structure

When using STL export, the output directory will contain:

```
output_dir/
├── organ1.stl
├── organ2.stl
├── ...
├── import_organs_blender.py    # Blender import script
└── task_summary.json          # Conversion summary
```

### Blender Import

1. Open Blender
2. Enable the "Import-Export STL files" add-on
3. Open Scripting workspace
4. Load and run the generated `import_organs_blender.py` script
5. Modify the `folder_path` variable to point to your STL directory
6. Run the script to import all organs with proper materials and organization

## Material System

The system includes pre-defined materials for different anatomical structures:

- **Bone**: Light brown color for all bone structures
- **Muscle**: Dark red for muscle tissues  
- **Liver**: Dark red-brown with variations for liver segments
- **Vessels**: Red for arteries, blue for veins
- **Organs**: Specific colors for heart, lungs, kidneys, etc.

## Advanced Features

### Liver Visualization

For liver segmentation results, a specialized Blender script is generated with:
- Individual colors for each liver segment (8 segments)
- Distinct materials for blood vessels and neoplasms  
- Organized collections for easy management
- Transparency settings for better visualization

### Mesh Optimization

STL files are generated with:
- Configurable smoothing (default: 10 iterations)
- Mesh reduction for smaller file sizes (default: 90% retention)
- Proper scaling for Blender import (1/50th scale)

## Compatibility

- **3D Slicer**: STL files are fully compatible with 3D Slicer for medical visualization
- **Blender**: Generated scripts work with Blender 3.0+ with STL import add-on enabled
- **Other 3D Software**: Standard STL format works with most 3D modeling software

## Technical Details

### Dependencies
- **VTK**: Required for STL generation and mesh processing
- **nibabel**: For NIfTI file handling (already included in TotalSegmentator)
- **numpy**: For data processing (already included in TotalSegmentator)

### Performance
- Multi-threaded processing when possible
- Automatic memory management for large datasets
- Fallback to NIfTI format if STL conversion fails

### File Formats
- **Input**: NIfTI (.nii.gz) segmentation masks
- **Output**: STL files + Blender Python scripts + JSON summaries
- **Compatibility**: Works with existing TotalSegmentator workflows

## Examples

### Example 1: Liver Segmentation Visualization

```bash
# Run liver segmentation
TotalSegmentator -i ct_scan.nii.gz -o liver_output --task liver_segments -ot stl

# Process additional liver tasks  
TotalSegmentator -i ct_scan.nii.gz -o liver_vessels --task liver_vessels -ot stl

# Combine and organize results
totalseg_process_liver -i combined_results -f stl
```

### Example 2: Full Body Visualization

```bash
# Generate full body segmentation as STL
TotalSegmentator -i body_scan.nii.gz -o body_stl --task total -ot stl

# Import into Blender using the generated script
# (Open Blender, run body_stl/import_organs_blender.py)
```

## Troubleshooting

### Common Issues

1. **VTK Import Error**: Install VTK with `pip install vtk`
2. **Memory Issues**: Reduce mesh resolution or use smaller ROI subsets
3. **Blender Import**: Ensure STL import add-on is enabled in Blender preferences
4. **Large Files**: Use mesh reduction settings to reduce STL file sizes

### Performance Tips

- Use `--roi_subset` to process only needed organs
- Adjust mesh reduction factor for balance between quality and file size
- Use multi-threading with `--nr_thr_saving` for faster processing

## Credits

This functionality incorporates techniques and color schemes from:
- @tk1971-Jpn/Import-organ-STL-data-into-Blender repository
- Standard medical visualization color conventions
- VTK mesh processing algorithms