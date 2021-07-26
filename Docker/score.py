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


def run_captk(path_to_captk, pred, gold, tmp):
    """
    Run BraTS Similarity Metrics computation of prediction scan
    against goldstandard.
    """
    cmd = [
        path_to_captk,
        "-i", pred,
        "-lsb", gold,
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
    scores = re.search(f"{region}.*", res).group().split(",")
    dice = scores[2]
    haus = scores[5]
    sens = scores[7]
    spec = scores[9]
    return {
        f"Dice_{region}": dice, f"Hausdorff95_{region}": haus,
        f"Sensitivity_{region}": sens, f"Specificity_{region}": spec
    }


def get_scores(tmp):
    """Get scores for three regions: ET, WT, and TC."""
    with open(tmp) as f:
        res = f.read()
        et_scores = extract_metrics(res, "ET")
        wt_scores = extract_metrics(res, "WT")
        tc_scores = extract_metrics(res, "TC")
        return {**et_scores, **wt_scores, **tc_scores}


def main():
    """Main function."""
    args = get_args()
    run_captk(args.captk_path, args.predictions_file,
              args.goldstandard_file, args.tmp)
    results = get_scores(args.tmp)
    os.remove(args.tmp)  # Remove file, as it's no longer needed

    with open(args.output, "w") as out:
        out.write(json.dumps(
            {**results, "submission_status": "ACCEPTED"}
        ))


if __name__ == "__main__":
    main()
