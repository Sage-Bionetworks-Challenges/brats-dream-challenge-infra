"""Scoring script for Task 1.

Run `BraTS Similarity Metrics Computation` command from CaPTk and return:
  - Dice
  - Hausdorff95
  - Overlap
  - Sensitivity
"""
import os
import argparse


def get_args():
    """Set up command-line interface and get arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--predictions_file",
                        type=str, required=True)
    parser.add_argument("-g", "--goldstandard_file",
                        type=str, required=True)
    parser.add_argument("-o", "--output",
                        type=str, default="results.csv")
    return parser.parse_args()


def main():
    args = get_args()
    print("success!")


if __name__ == "__main__":
    main()
