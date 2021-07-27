#!/usr/bin/env python3
"""Scoring script for Task 1.

Run `BraTS Similarity Metrics Computation` command from CaPTk and return:
  - Dice
  - Hausdorff95
  - Overlap
  - Sensitivity
"""
import os
import re
import subprocess
import argparse
import json
import zipfile

import pandas as pd


def get_args():
    """Set up command-line interface and get arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--predictions_file",
                        type=str, required=True)
    parser.add_argument("-g", "--goldstandard_file",
                        type=str, required=True)
    parser.add_argument("-o", "--output",
                        type=str, default="results.json")
    parser.add_argument("-c", "--captk_path",
                        type=str, required=True)
    parser.add_argument("-t", "--tmp",
                        type=str, default="tmp_results.csv")
    return parser.parse_args()


def unzip_file(z, pred):
    """Unzip groundtruth file that corresponds to prediction file."""
    scan_number = re.search(r"_(\d{3}).nii.gz$", pred).group(1)
    with zipfile.ZipFile(z) as zip_ref:
        zipped_file = [f for f in zip_ref.namelist()
                       if f.endswith(f"{scan_number}_seg.nii.gz")][0]
        filepath = zip_ref.extract(zipped_file, ".")
    return filepath


def run_captk(path_to_captk, pred, gold, tmp):
    """
    Run BraTS Similarity Metrics computation of prediction scan
    against goldstandard.
    """
    cmd = [
        os.path.join(path_to_captk, "bin/Utilities"),
        "-i", gold,
        "-lsb", pred,
        "-o", tmp
    ]
    subprocess.check_call(cmd)


def extract_metrics(res, region):
    """Find and return the metrics of interest.

    Metrics wanted:
      - Dice score
      - Hausdorff distance
      - specificity
      - sensitivity
    """
    scores = res.loc[region]
    dice = scores["Dice"]
    haus = scores["Hausdorff95"]
    sens = scores["Sensitivity"]
    spec = scores["Specificity"]
    return {
        f"Dice_{region}": dice, f"Hausdorff95_{region}": haus,
        f"Sensitivity_{region}": sens, f"Specificity_{region}": spec
    }


def get_scores(tmp):
    """Get scores for three regions: ET, WT, and TC."""
    res = pd.read_csv(tmp, index_col="Labels")
    et_scores = extract_metrics(res, "ET")
    wt_scores = extract_metrics(res, "WT")
    tc_scores = extract_metrics(res, "TC")
    return {**et_scores, **wt_scores, **tc_scores}


def main():
    """Main function."""
    args = get_args()
    pred = args.predictions_file
    gold = unzip_file(args.goldstandard_file, pred)

    run_captk(args.captk_path, pred,
              gold, args.tmp)
    results = get_scores(args.tmp)
    os.remove(args.tmp)  # Remove file, as it's no longer needed

    with open(args.output, "w") as out:
        out.write(json.dumps(
            {**results, "submission_status": "ACCEPTED"}
        ))


if __name__ == "__main__":
    main()
