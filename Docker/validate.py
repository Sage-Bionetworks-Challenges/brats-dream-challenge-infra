#!/usr/bin/env python3
"""Validation script for Task 1.

Predictions file must be a tarball or zipped archive of NIfTI files
(*.nii.gz). Each NIfTI file must have an ID in its filename.
"""
import argparse
import json
import tarfile
import zipfile


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


def get_images(submission):
    """Untar or unzip submission file."""
    if zipfile.is_zipfile(submission):
        with zipfile.ZipFile(submission) as zip_ref:
            imgs = zip_ref.namelist()
    elif tarfile.is_tarfile(submission):
        with tarfile.TarFile(submission) as tar_ref:
            imgs = tar_ref.getnames()
    else:
        imgs = []
    return imgs


def validate_file_format(imgs):
    """Check that all files are NIfTI files (*.nii.gz)."""
    error = []
    if not all(f.endswith(".nii.gz") for f in imgs):
        error = ["Not all files in the archive are NIfTI files (*.nii.gz)."]
    return error


def validate_filenames(imgs):
    """Check that there is a NIfTI file for every scan ID (001-166)."""
    missing_ids = []
    scan_ids = range(1, 167)
    for i in scan_ids:
        scan_id = f"{i:03d}"
        if not any(scan_id in f for f in imgs):
            missing_ids.append(scan_id)

    error = []
    if missing_ids:
        error = [("Missing NIfTI file for the following IDs: "
                  f"{', '.join(missing_ids)}")]
    return error


def main():
    """Main function."""
    args = get_args()

    invalid_reasons = []

    imgs = get_images(args.predictions_file)
    if imgs:
        invalid_reasons.extend(validate_file_format(imgs))
        invalid_reasons.extend(validate_filenames(imgs))
    else:
        invalid_reasons.append(
            "Submission must be a tarball or zipped archive of NIfTI files."
        )
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
