#!/usr/bin/env python3
"""Validation script for Task 1.

Predictions file must be a tarball or zipped archive of NIfTI files
(*.nii.gz). Each NIfTI file must have an ID in its filename.
"""
import argparse
import json
import tarfile
import zipfile

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


def get_images(submission):
    """Get filenames of images in the archived file."""
    if zipfile.is_zipfile(submission):
        with zipfile.ZipFile(submission) as zip_ref:
            zip_ref.extractall(".")
            imgs = zip_ref.namelist()
    elif tarfile.is_tarfile(submission):
        with tarfile.TarFile(submission) as tar_ref:
            tar_ref.extractall(".")
            imgs = tar_ref.getnames()
    else:
        imgs = []

    # Filter out top-level folder name, in case participant archived
    # a folder rather than bundle of files and/or participant used
    # MacOS to archive.
    return [img for img in imgs
            if not img.endswith("/") and not img.startswith("__MACOSX/")
            and not img.endswith(".DS_Store")]


def check_file_contents(img):
    """Check that the file can be opened as NIfTI."""
    try:
        nib.load(img)
        return "valid"
    except nib.filebasedimages.ImageFileError:
        return "invalid"


def validate_file_format(imgs):
    """Check that all files are NIfTI files (*.nii.gz)."""
    error = []
    if all(f.endswith(".nii.gz") for f in imgs):

        # Ensure that all file contents are NIfTI.
        if not all(check_file_contents(img) == "valid" for img in imgs):
            error = [("One or more predictions cannot be opened as a "
                      "NIfTI file.")]
    else:
        error = ["Not all files in the archive are NIfTI files (*.nii.gz)."]
    return error


def validate_filenames(imgs):
    """Check that every NIfTI filename ends with a case ID."""
    error = []

    case_ids = [img[-12:-7] for img in imgs]
    if all(case_id.isdigit() for case_id in case_ids):

        # Check that all case IDs are unique.
        if len(set(case_ids)) != len(case_ids):
            error = ["Duplicate predictions found for one or more cases."]
    else:
        error = [("Not all filenames in the archive end with a case "
                  "ID (*{5-digit ID}.nii.gz).")]
    return error


def main():
    """Main function."""
    args = get_args()

    invalid_reasons = []

    entity_type = args.entity_type.split(".")[-1]
    if entity_type != "FileEntity":
        invalid_reasons.append(
            f"Submission must be a File, not {entity_type}."
        )
    else:
        imgs = get_images(args.predictions_file)
        if imgs:
            invalid_reasons.extend(validate_file_format(imgs))
            invalid_reasons.extend(validate_filenames(imgs))
        else:
            invalid_reasons.append(
                "Submission must be a tarball or zipped archive "
                "containing at least one NIfTI file."
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
