# BraTS Challenge (2021, 2022) - Task 1

| 2021                                      | 2022                                      |
| ----------------------------------------- | ----------------------------------------- |
| [link](https://www.synapse.org/brats2021) | [link](https://www.synapse.org/brats2022) |

This series of challenges is split into two phases:

- Validation (data) phase
- Testing (data) phase

The **Validation phase** will utilize the CWL workflow,
[`validation-phase-workflow.cwl`], accepting a group of prediction files and
scoring them against the ground truth files with [CaPTk].

The **Testing phase** will utilize the CWL workflow,
[`testing-phase-workflow.cwl`], accepting a Docker model to first infer the
predictions, then scoring those predictions with [CaPTk].

Metrics are returned in a JSON file, `results.json` and are the same for
both workflows:

- Dice similarity coefficient
- Hausdorff distance, 95%
- Sensitivity
- Specificity
- Precision _\*\*new for 2022\*\*_

## Usage

`validation-phase-workflow.cwl` and `testing-phase-workflow.cwl` were both
written with the intention of being utilized with the [Synapse platform].
You may also locally run the validation and scoring steps on your machine,
if desired.

### Requirements

- Python 3.7+
- [CaPTk 1.8.1+]

Alternatively, if you do not wish to install Python and/or CaPTk, you may
perform validation and scoring using the challenge's [evaluation model]
([Docker] and Synapse account required).

### Running with Python

The Python scripts are contained in the `Docker/` directory of this repository.
After cloning, change directories to `Docker/`:

    git clone https://github.com/Sage-Bionetworks-Challenges/brats-dream-challenge-infra.git
    cd brats-dream-challenge-infra/Docker/

#### Validation

To validate a submission, run the following command:

    python validate.py \
      -g <filepath to tarball/zipped archive of ground truth> \
      -p <filepath to tarball/zipped archive of predictions> \
      -e <Synapse entity type of submission>

Note that the `-e` flag is relevant to the Synapse platform only; it indicates
the submission type, e.g. a file, Docker container, folder, etc. In order to
not incorrectly label the submission as "INVALID" on your machine, manually
pass `FileEntity` for `-e`.

For example:

    python validate.py \
      -g ~/goldstandard.zip \
      -p ~/predictions.zip \
      -e FileEntity

Results are returned in a JSON file, `results.json`, where:

- submission_status - indicates whether the submission is valid (`VALIDATED`
  or `INVALID`)
- submission_errors - list of validation errors, if any

#### Scoring

To score a submission, run the following command:

    python score.py \
      --parent_id <Synapse ID to a folder storing logs> \
      -s <filepath to Synapse configuration file> \
      -c <filepath to CaPTk application> \
      -g <filepath to tarball/zipped archive of ground truth> \
      -p <filepath to tarball/zipped archive of predictions>

For example:

    python score.py \
      --parent_id syn26003183 \
      -s ~/.synapseConfig \
      -c /Applications/CaPTk_1.8.1.app/Contents \
      -g ~/goldstandard.zip \
      -p ~/predictions.zip

Results are returned in two files, where:

- `results.json` is a JSON file containing metric averages across all scored
  segmentations, along with additional information such as submission status,
  number of cases evaluated, etc.
- `scores.csv` is a CSV file containing individual metric scores of each
  segmentation

## Running with Docker

To use the [evaluation model], first log in to the Synapse Docker hub and get
the image:

    docker login docker.synapse.org
    docker pull docker.synapse.org/syn25829067/evaluation

#### Validation

To validate a submission, run the following command:

    docker run \
      -v /path/to/goldstandard:/goldstandard.zip:ro \
      -v /path/to/predictions:/predictions.zip:ro \
      docker.synapse.org/syn25829067/evaluation:v1 \
        validate.py -e FileEntity

where `/path/to/goldstandard` and `/path/to/predictions` are the absolute
paths to the ground truth and prediction tarballs/zipped archives, respectively.

#### Scoring

To score a submission, run the following command:

    docker run \
      -v /path/to/.synapseConfig:/.synapseConfig \
      -v /path/to/goldstandard:/goldstandard.zip:ro \
      -v /path/to/predictions:/predictions.zip:ro \
      docker.synapse.org/syn25829067/evaluation:v1 \
        score.py --parent_id syn21246349

where `/path/to/.synapseConfig`, `/path/to/goldstandard`, and
`/path/to/predictions` are the absolute paths to the Synapse configuration
file, ground truth and prediction tarballs/zipped archive.

<!-- Links -->

[`validation-phase-workflow.cwl`]: https://raw.githubusercontent.com/Sage-Bionetworks-Challenges/brats-dream-challenge-infra/main/validation-phase-workflow.cwl
[`testing-phase-workflow.cwl`]: https://raw.githubusercontent.com/Sage-Bionetworks-Challenges/brats-dream-challenge-infra/main/testing-phase-workflow.cwl
[captk]: https://cbica.github.io/CaPTk/
[synapse platform]: https://www.synapse.org/
[captk 1.8.1+]: https://cbica.github.io/CaPTk/Download.html
[evaluation model]: https://www.synapse.org/#!Synapse:syn27788111
[docker]: https://docs.docker.com/get-docker/
