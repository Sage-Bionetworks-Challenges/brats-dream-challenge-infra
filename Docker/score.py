#!/usr/bin/env python3
"""Scoring script for Task 1.

Run `BraTS Similarity Metrics Computation` command from CaPTk and return:
  - Dice
  - Hausdorff95
  - Sensitivity
  - Specificity
  - Precision
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
                        type=str, default="/.synapseConfig")
    parser.add_argument("-p", "--predictions_file",
                        type=str, default="/predictions.zip")
    parser.add_argument("-g", "--goldstandard_file",
                        type=str, default="/goldstandard.zip")
    parser.add_argument("-o", "--output",
                        type=str, default="results.json")
    parser.add_argument("-c", "--captk_path",
                        type=str, default="/work/CaPTk")
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


def extract_metrics(tmp, scan_id, prefix):
    """Get scores for three regions: ET, WT, and TC.

    Metrics wanted:
      - Dice score
      - Hausdorff distance
      - specificity
      - sensitivity
      - precision
    """
    res = (
        pd.read_csv(tmp, index_col="Labels")
        .filter(items=["Labels", "Dice", "Hausdorff95",
                       "Sensitivity", "Specificity",
                       "Precision"])
        .filter(items=["ET", "WT", "TC"], axis=0)
        .reset_index()
        .assign(scan_id=f"{prefix}_{scan_id}")
        .pivot(index="scan_id", columns="Labels")
    )
    res.columns = ["_".join(col).strip() for col in res.columns]
    return res


def score(parent, pred_lst, captk_path, dataset="BraTS2021", tmp_output="tmp.csv"):
    """Compute and return scores for each scan."""
    scores = []
    filtered_preds = [f for f in pred_lst
                      if os.path.split(f)[1].startswith(dataset)]
    for pred in filtered_preds:
        scan_id = pred[-12:-7]
        gold = os.path.join(parent, f"{dataset}_{scan_id}_seg.nii.gz")
        try:
            run_captk(captk_path, pred, gold, tmp_output)
            scan_scores = extract_metrics(tmp_output, scan_id, dataset)
            os.remove(tmp_output)  # Remove file, as it's no longer needed
        except subprocess.CalledProcessError:
            # If no output found, give penalized scores.
            scan_scores = (
                pd.DataFrame({
                    "scan_id": [f"{dataset}_{scan_id}*"],
                    "Dice_ET": [0], "Dice_TC": [0], "Dice_WT": [0],
                    "Hausdorff95_ET": [374], "Hausdorff95_TC": [374],
                    "Hausdorff95_WT": [374], "Sensitivity_ET": [0],
                    "Sensitivity_TC": [0], "Sensitivity_WT": [0],
                    "Specificity_ET": [0], "Specificity_TC": [0],
                    "Specificity_WT": [0], "Precision_ET": [0],
                    "Precision_TC": [0], "Precision_WT": [0]
                })
                .set_index("scan_id")
            )
        scores.append(scan_scores)
    return pd.concat(scores).sort_values(by="scan_id")


def compile_and_upload(syn, parent, results, prefix=""):
    # Get number of segmentations predicted by participant, number of
    # segmentation that could not be scored, and number of segmentations
    # that were scored.
    cases_predicted = len(results.index)
    flagged_cases = int(results.reset_index().scan_id.str.count(r"\*").sum())
    cases_evaluated = cases_predicted - flagged_cases

    # Aggregate scores.
    results.loc["mean"] = results.mean()
    results.loc["sd"] = results.std()
    results.loc["median"] = results.median()
    results.loc["25quantile"] = results.quantile(q=0.25)
    results.loc["75quantile"] = results.quantile(q=0.75)

    # CSV file of scores for all scans.
    filename = f"{prefix}all_scores.csv"
    results.to_csv(filename)
    csv = synapseclient.File(filename, parent=parent)
    csv = syn.store(csv)
    return {
        f"{prefix}cases_evaluated": cases_evaluated,
        f"{prefix}submission_scores": csv.id
    }


def main():
    """Main function."""
    args = get_args()
    preds = utils.unzip_file(args.predictions_file)
    golds = utils.unzip_file(args.goldstandard_file)
    dir_name = os.path.split(golds[0])[0]

    scores = score(dir_name, preds, args.captk_path)
    ssa_scores = score(dir_name, preds, args.captk_path, dataset="BraTS_SSA")

    syn = synapseclient.Synapse(configPath=args.synapse_config)
    syn.login(silent=True)
    results = compile_and_upload(syn, args.parent_id, scores)
    ssa_results = compile_and_upload(syn, args.parent_id,
                                     ssa_scores, prefix="ssa_")

    # Results file for annotations.
    with open(args.output, "w") as out:
        res_dict = {  # **results.loc["mean"].to_dict(),
            **results, **ssa_results,
            "submission_status": "SCORED"}
        res_dict = {k: v for k, v in res_dict.items() if not pd.isna(v)}
        out.write(json.dumps(res_dict))


if __name__ == "__main__":
    main()
