#!/usr/bin/env python3
"""Scoring script for Task 1.

Run `BraTS Similarity Metrics Computation` command from CaPTk and return:
  - Dice
  - Hausdorff95
  - Overlap
  - Sensitivity
"""
import os
import subprocess
import argparse
import json

import pandas as pd
import synapseclient
import utils


def get_args():
    """Set up command-line interface and get arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--parent_id",
                        type=str, required=True)
    parser.add_argument("-s", "--synapse_config",
                        type=str, required=True)
    parser.add_argument("-p", "--predictions_file",
                        type=str, required=True)
    parser.add_argument("-g", "--goldstandard_file",
                        type=str, required=True)
    parser.add_argument("-o", "--output",
                        type=str, default="results.json")
    parser.add_argument("-c", "--captk_path",
                        type=str, required=True)
    return parser.parse_args()


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


def extract_metrics(tmp, scan_id):
    """Get scores for three regions: ET, WT, and TC.

    Metrics wanted:
      - Dice score
      - Hausdorff distance
      - specificity
      - sensitivity
    """
    res = (
        pd.read_csv(tmp, index_col="Labels")
        .filter(items=["Labels", "Dice", "Hausdorff95",
                       "Sensitivity", "Specificity"])
        .filter(items=["ET", "WT", "TC"], axis=0)
        .reset_index()
        .assign(scan_id=scan_id)
        .pivot(index="scan_id", columns="Labels")
    )
    res.columns = ["_".join(col).strip() for col in res.columns.values]
    return res


def score(pred_lst, gold_lst, captk_path, tmp_output="tmp.csv"):
    """Compute and return scores for each scan."""
    scores = []
    for pred in pred_lst:
        scan_id = pred[-12:-7]
        gold = [f for f in gold_lst
                if f.endswith(f"{scan_id}_seg.nii.gz")][0]
        run_captk(captk_path, pred, gold, tmp_output)
        scan_scores = extract_metrics(tmp_output, scan_id)
        scores.append(scan_scores)
        os.remove(tmp_output)  # Remove file, as it's no longer needed
    return pd.concat(scores).sort_values(by="scan_id")


def main():
    """Main function."""
    args = get_args()
    preds = utils.unzip_file(args.predictions_file)
    golds = utils.unzip_file(args.goldstandard_file)

    results = score(preds, golds, args.captk_path)
    cases = len(results.index)
    results.loc["mean"] = results.mean()
    results.loc["sd"] = results.std()
    results.loc["median"] = results.median()
    results.loc["25quantile"] = results.quantile(q=0.25)
    results.loc["75quantile"] = results.quantile(q=0.75)

    # CSV file of scores for all scans.
    results.to_csv("all_scores.csv")
    syn = synapseclient.Synapse(configPath=args.synapse_config)
    syn.login(silent=True)
    csv = synapseclient.File("all_scores.csv", parent=args.parent_id)
    csv = syn.store(csv)

    # Results file for annotations.
    with open(args.output, "w") as out:
        out.write(json.dumps(
            {**results.loc["mean"].to_dict(),
             "cases_evaluated": cases,
             "submission_scores": csv.id,
             "submission_status": "SCORED"}
        ))


if __name__ == "__main__":
    main()
