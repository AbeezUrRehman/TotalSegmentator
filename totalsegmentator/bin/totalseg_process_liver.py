#!/usr/bin/env python

import argparse
from pathlib import Path

from totalsegmentator.liver_processing import process_liver_segmentation_results


def main():
    parser = argparse.ArgumentParser(
        description="Process liver segmentation results for improved 3D visualization",
        epilog="This tool converts liver segmentation results to STL format with Blender import scripts."
    )
    
    parser.add_argument("-i", "--input", metavar="directory", dest="input_dir",
                        help="Input directory containing liver segmentation results",
                        type=lambda p: Path(p).absolute(), required=True)
    
    parser.add_argument("-f", "--format", choices=["stl", "nifti"],
                        help="Output format (stl for Blender/3D Slicer, nifti to keep original)",
                        default="stl")
    
    parser.add_argument("--no-blender-scripts", action="store_true",
                        help="Do not generate Blender import scripts",
                        default=False)
    
    parser.add_argument("-q", "--quiet", action="store_true",
                        help="Suppress output messages",
                        default=False)
    
    args = parser.parse_args()
    
    if not args.input_dir.exists():
        print(f"Error: Input directory {args.input_dir} does not exist")
        return 1
    
    if not args.quiet:
        print(f"Processing liver segmentation results in: {args.input_dir}")
        print(f"Output format: {args.format}")
        if args.format == "stl" and not args.no_blender_scripts:
            print("Blender import scripts will be generated")
    
    try:
        process_liver_segmentation_results(
            results_dir=args.input_dir,
            output_format=args.format,
            generate_blender_scripts=not args.no_blender_scripts
        )
        
        if not args.quiet:
            print("Processing completed successfully!")
        
        return 0
        
    except Exception as e:
        print(f"Error during processing: {e}")
        return 1


if __name__ == "__main__":
    exit(main())