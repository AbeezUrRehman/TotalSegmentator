"""
Enhanced liver vessel post-processing utilities with robust fallbacks.

This module now:
- Accepts a missing or unreadable liver mask and falls back to a full-volume mask.
- Handles empty vessel predictions gracefully.
- Produces metadata even when fallback logic is used.
"""

import json
import numpy as np
import nibabel as nib
from pathlib import Path
import datetime
import warnings
try:
    from scipy import ndimage
    from scipy.ndimage import binary_closing, binary_dilation, binary_erosion, distance_transform_edt
    _HAVE_SCIPY = True
except ImportError:
    _HAVE_SCIPY = False
    warnings.warn("scipy not available - enhanced morphological operations disabled")


class EnhancedLiverVesselProcessor:
    def __init__(self, contrast_phase=None, min_component_size=40, 
                 vessel_hu_range=(30, 200), enhancement_iterations=2):
        self.contrast_phase = contrast_phase
        self.min_component_size = min_component_size
        self.vessel_hu_range = vessel_hu_range  # Typical enhanced vessel HU range
        self.enhancement_iterations = enhancement_iterations

    def enhance_vessel_connectivity(self, vessel_mask, liver_mask):
        """Enhanced vessel connectivity with morphological operations."""
        # Restrict vessels to liver region (if liver_mask is not empty)
        if liver_mask.sum() > 0:
            vessel_mask = vessel_mask * liver_mask

        # Early return if empty
        if vessel_mask.sum() == 0:
            return vessel_mask

        # Enhanced morphological processing with scipy
        if _HAVE_SCIPY:
            vessel_mask = self._morphological_enhancement(vessel_mask)
            vessel_mask = self._remove_small_components(vessel_mask)
        else:
            # Fallback: basic component removal without scipy
            warnings.warn("Using basic enhancement - install scipy for better results")
        
        return vessel_mask

    def _morphological_enhancement(self, vessel_mask):
        """Apply morphological operations to improve vessel connectivity."""
        if not _HAVE_SCIPY:
            return vessel_mask
        
        enhanced = vessel_mask.copy()
        
        # Create structuring elements for different operations
        # Small spherical structuring element for closing gaps
        sphere_small = ndimage.generate_binary_structure(3, 1)  # 6-connectivity
        sphere_medium = ndimage.generate_binary_structure(3, 2)  # 18-connectivity
        
        # 1. Close small gaps in vessels
        enhanced = binary_closing(enhanced, structure=sphere_small, iterations=1)
        
        # 2. Fill small holes within vessel structures
        enhanced = ndimage.binary_fill_holes(enhanced)
        
        # 3. Light dilation to connect nearby vessel segments
        enhanced = binary_dilation(enhanced, structure=sphere_small, iterations=1)
        
        # 4. Slight erosion to restore original size while keeping connections
        enhanced = binary_erosion(enhanced, structure=sphere_small, iterations=1)
        
        # 5. Final closing with medium element for better connectivity
        enhanced = binary_closing(enhanced, structure=sphere_medium, iterations=1)
        
        return enhanced.astype(np.uint8)

    def _remove_small_components(self, vessel_mask):
        """Remove small disconnected components."""
        if not _HAVE_SCIPY:
            return vessel_mask
            
        labeled, ncomp = ndimage.label(vessel_mask)
        if ncomp == 0:
            return vessel_mask
            
        # Calculate component sizes
        sizes = ndimage.sum(vessel_mask, labeled, range(1, ncomp + 1))
        
        # Remove components smaller than threshold
        for idx, sz in enumerate(sizes, start=1):
            if sz < self.min_component_size:
                vessel_mask[labeled == idx] = 0
                
        return vessel_mask

    def optimize_for_contrast_phase(self, ct_data, vessel_mask):
        """Intensity-based vessel enhancement using CT Hounsfield units."""
        if vessel_mask.sum() == 0:
            return vessel_mask
            
        enhanced = vessel_mask.copy()
        
        # Apply intensity-based refinement
        enhanced = self._intensity_based_refinement(ct_data, enhanced)
        
        # Apply vessel centerline enhancement
        enhanced = self._centerline_enhancement(ct_data, enhanced)
        
        return enhanced

    def _intensity_based_refinement(self, ct_data, vessel_mask):
        """Refine vessel mask using CT intensity values."""
        if not _HAVE_SCIPY:
            return vessel_mask
            
        # Create intensity-based vessel probability map
        hu_min, hu_max = self.vessel_hu_range
        intensity_prob = np.zeros_like(ct_data, dtype=np.float32)
        
        # Sigmoid function for smooth intensity weighting
        # Vessels typically have higher HU values when contrast-enhanced
        intensity_prob = 1.0 / (1.0 + np.exp(-0.1 * (ct_data - hu_min)))
        intensity_prob[ct_data > hu_max] = 1.0  # Saturate at high intensities
        intensity_prob[ct_data < 0] = 0.0  # Suppress negative HU values
        
        # Apply intensity weighting to vessel regions
        if vessel_mask.sum() > 0:
            # Get distance from vessel edges for gradient weighting
            vessel_distance = distance_transform_edt(vessel_mask)
            
            # Create expansion region around existing vessels
            expansion_radius = 3  # voxels
            expansion_mask = vessel_distance <= expansion_radius
            
            # Weight by both intensity and distance from existing vessels
            expansion_prob = intensity_prob * expansion_mask
            
            # Add high-intensity regions near existing vessels
            threshold = 0.7  # Probability threshold for expansion
            vessel_expansion = expansion_prob > threshold
            
            # Combine original vessels with intensity-based expansion
            enhanced = vessel_mask | vessel_expansion.astype(np.uint8)
        else:
            enhanced = vessel_mask
            
        return enhanced

    def _centerline_enhancement(self, ct_data, vessel_mask):
        """Enhance vessel centerlines and connectivity."""
        if not _HAVE_SCIPY or vessel_mask.sum() == 0:
            return vessel_mask
            
        # Calculate distance transform to find centerlines
        distance_map = distance_transform_edt(vessel_mask)
        
        # Find local maxima as potential centerlines
        # Use a small neighborhood for local maxima detection
        from scipy.ndimage import maximum_filter
        local_maxima = maximum_filter(distance_map, size=3) == distance_map
        local_maxima = local_maxima & (distance_map > 1)  # Exclude boundary voxels
        
        # Enhance connectivity along centerlines
        centerline_mask = local_maxima & (vessel_mask > 0)
        
        if centerline_mask.sum() > 0:
            # Dilate centerlines to improve connectivity
            enhanced_centerlines = binary_dilation(centerline_mask, iterations=1)
            
            # Add enhanced centerlines back to vessel mask
            enhanced = vessel_mask | enhanced_centerlines.astype(np.uint8)
        else:
            enhanced = vessel_mask
            
        return enhanced


def _load_nifti_safely(path: Path, purpose: str):
    try:
        img = nib.load(str(path))
        return img
    except FileNotFoundError:
        warnings.warn(f"[EnhancedLiver] {purpose} file not found at {path}. Using fallback.")
    except Exception as e:
        warnings.warn(f"[EnhancedLiver] Failed loading {purpose} ({path}): {e}. Using fallback.")
    return None


def _create_full_mask_like(img):
    data = img.get_fdata()
    return np.ones(data.shape, dtype=np.uint8)


def _estimate_contrast_phase(ct_data, liver_mask=None):
    """Estimate contrast phase based on CT intensity characteristics."""
    if liver_mask is not None and liver_mask.sum() > 0:
        # Analyze intensity within liver region
        liver_intensities = ct_data[liver_mask > 0]
        mean_liver_hu = np.mean(liver_intensities)
        std_liver_hu = np.std(liver_intensities)
        
        # Heuristic classification based on liver enhancement
        if mean_liver_hu > 100:
            return "arterial"  # High enhancement
        elif mean_liver_hu > 60:
            return "portal_venous"  # Moderate enhancement  
        elif mean_liver_hu > 40:
            return "delayed"  # Mild enhancement
        else:
            return "unenhanced"
    else:
        # Global image characteristics
        mean_hu = np.mean(ct_data)
        if mean_hu > 50:
            return "enhanced"
        else:
            return "unenhanced"


def _optimize_parameters_for_contrast(contrast_phase, base_params):
    """Optimize enhancement parameters based on detected contrast phase."""
    optimized = base_params.copy()
    
    if contrast_phase == "arterial":
        # Arterial phase: vessels are bright, use higher HU threshold
        optimized['vessel_hu_range'] = (50, 300)
        optimized['min_component_size'] = max(15, optimized['min_component_size'] - 5)
    elif contrast_phase == "portal_venous":
        # Portal venous: optimal for liver vessels
        optimized['vessel_hu_range'] = (30, 200)
        optimized['min_component_size'] = optimized['min_component_size']
    elif contrast_phase == "delayed":
        # Delayed phase: lower enhancement
        optimized['vessel_hu_range'] = (20, 150)
        optimized['min_component_size'] = max(10, optimized['min_component_size'] - 10)
    else:  # unenhanced
        # Non-contrast: rely more on morphology, less on intensity
        optimized['vessel_hu_range'] = (-50, 100)  # Broader range
        optimized['min_component_size'] = max(5, optimized['min_component_size'] - 15)
        
    return optimized


def process_enhanced_liver_vessels(
    input_path,
    output_path,
    liver_mask_path=None,
    device="auto",
    allow_fallback_full_liver=True,
    min_component_size=20,
    vessel_hu_range=(30, 200),
    enhancement_iterations=2
):
    """
    Run liver_vessels task + light enhancement and save output + metadata.

    Parameters
    ----------
    input_path : str or Path
        Path to CT NIfTI.
    output_path : str or Path
        Output NIfTI path for enhanced vessel mask.
    liver_mask_path : str or Path or None
        Optional precomputed liver mask. If missing/unreadable and allow_fallback_full_liver=True,
        a full-volume mask is used.
    device : str
        Device spec forwarded to underlying totalsegmentator calls.
    allow_fallback_full_liver : bool
        If True, absence of a liver mask will not crash; we use full volume.
    min_component_size : int
        Minimum size (voxels) for connected vessel components to keep.
    """
    from totalsegmentator.python_api import totalsegmentator

    input_path = Path(input_path)
    output_path = Path(output_path)

    ct_img = nib.load(str(input_path))
    ct_data = ct_img.get_fdata()

    # Liver mask handling
    liver_mask = None
    liver_mask_source = None
    if liver_mask_path is not None:
        liver_mask_img = _load_nifti_safely(Path(liver_mask_path), "liver mask")
        if liver_mask_img is not None:
            liver_mask = (liver_mask_img.get_fdata() > 0).astype(np.uint8)
            liver_mask_source = "provided"
    if liver_mask is None:
        if allow_fallback_full_liver:
            liver_mask = _create_full_mask_like(ct_img)
            liver_mask_source = "fallback_full_volume"
            warnings.warn("[EnhancedLiver] Using full-volume mask as fallback (not ideal for real inference).")
        else:
            raise FileNotFoundError("Liver mask missing and fallback disabled.")

    # Vessel prediction
    try:
        vessels_res_img = totalsegmentator(
            str(input_path),
            None,
            task="liver_vessels",
            ml=True,
            device=device,
            robust_crop=True
        )
        vessel_mask_raw = (vessels_res_img.get_fdata() == 1).astype(np.uint8)
        vessel_prediction_ok = True
    except Exception as e:
        warnings.warn(f"[EnhancedLiver] liver_vessels task failed: {e}. Creating empty mask.")
        vessel_mask_raw = np.zeros(ct_data.shape, dtype=np.uint8)
        vessel_prediction_ok = False

    # Estimate contrast phase and optimize parameters
    contrast_phase = _estimate_contrast_phase(ct_data, liver_mask)
    base_params = {
        'vessel_hu_range': vessel_hu_range,
        'min_component_size': min_component_size,
        'enhancement_iterations': enhancement_iterations
    }
    optimized_params = _optimize_parameters_for_contrast(contrast_phase, base_params)
    
    processor = EnhancedLiverVesselProcessor(
        min_component_size=optimized_params['min_component_size'],
        vessel_hu_range=optimized_params['vessel_hu_range'],
        enhancement_iterations=optimized_params['enhancement_iterations'],
        contrast_phase=contrast_phase
    )
    vessel_mask_enh = processor.enhance_vessel_connectivity(vessel_mask_raw, liver_mask)
    vessel_mask_enh = processor.optimize_for_contrast_phase(ct_data, vessel_mask_enh)

    # Save enhanced vessel mask
    out_img = nib.Nifti1Image(vessel_mask_enh, ct_img.affine, ct_img.header)
    nib.save(out_img, str(output_path))

    voxel_volume = float(np.prod(ct_img.header.get_zooms()))
    
    # Calculate enhancement statistics
    original_voxels = int(vessel_mask_raw.sum())
    enhanced_voxels = int(vessel_mask_enh.sum())
    enhancement_ratio = enhanced_voxels / original_voxels if original_voxels > 0 else 0.0
    
    metadata = {
        "input": str(input_path),
        "output": str(output_path),
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "detected_contrast_phase": contrast_phase,
        "original_vessel_voxels": original_voxels,
        "enhanced_vessel_voxels": enhanced_voxels,
        "enhancement_ratio": enhancement_ratio,
        "voxel_volume_mm3": voxel_volume,
        "original_volume_mm3": float(original_voxels * voxel_volume),
        "enhanced_volume_mm3": float(enhanced_voxels * voxel_volume),
        "enhancement_steps": [
            "liver_intersection", 
            "morphological_enhancement", 
            "small_component_removal",
            "intensity_based_refinement",
            "centerline_enhancement"
        ],
        "liver_mask_source": liver_mask_source,
        "vessel_prediction_ok": vessel_prediction_ok,
        "requested_parameters": {
            "min_component_size": min_component_size,
            "vessel_hu_range": vessel_hu_range,
            "enhancement_iterations": enhancement_iterations
        },
        "optimized_parameters": optimized_params,
        "scipy_available": _HAVE_SCIPY,
    }

    meta_path = output_path.with_name(output_path.name.replace(".nii.gz", "_metadata.json"))
    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2)

    return out_img, metadata