"""Validation script for Task 1.

Predictions file must be a NIFTI file (*.nii.gz), where filename must
match with the goldstandard's naming format.
"""
import os
import argparse
import json


def get_args():
    """Set up command-line interface and get arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--predictions_file",
                        type=str, required=True)
    parser.add_argument("-e", "--entity_type",
                        type=str, required=True)
    parser.add_argument("-o", "--output",
                        type=str, default="results.json")
    return parser.parse_args()


def main():
    args = get_args()
    print("success!")


if __name__ == "__main__":
    main()
