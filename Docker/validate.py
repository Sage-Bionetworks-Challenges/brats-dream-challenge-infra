"""Validation script for Task 1.

Predictions file must be a NIfTI file (*.nii.gz), where filename must
match with the goldstandard's naming format.
"""
import os
import argparse
import json

import nibabel as nib


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


def validate_img(img):
    """Validate image file."""
    return []


def main():
    args = get_args()

    invalid_reasons = []
    try:
        img = nib.load(args.predictions_file)
    except nib.filebasedimages.ImageFileError:
        invalid_reasons.append(
            ("Submitted file is not an acceptable neuroimaging file format. "
             "Double-check that you are submitting a NIfTI file (*.nii.gz).")
        )
    else:
        invalid_reasons.extend(validate_img(img))

    status = "INVALID" if invalid_reasons else "VALIDATED"

    with open(args.output, "w") as out:
        out.write(json.dumps(
            {
                "submission_status": status,
                "submission_errors": "\n".join(invalid_reasons)
            }
        ))


if __name__ == "__main__":
    main()
