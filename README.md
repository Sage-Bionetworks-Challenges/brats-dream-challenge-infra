# BraTS Challenge (2021, 2022)

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
perform validation and scoring using our [evaluation container] ([Docker]
required).

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

Note that `-e` flag is how the Synapse platform ensures that the submission
is a file and not a Docker container, folder, etc. In order to not incorrectly
label the submission as "INVALID" on your machine, manually enter `FileEntity`.

For example:

    python validate.py \
      -g ~/goldstandard.zip \
      -p ~/predictions.zip \
      -e FileEntity

Results are returned in a JSON file, `results.json`, where:

- submission_status - indicates whether the submission is valid or not
- submission_errors - list of validation errors, if any

#### Scoring

To score a submission, run the following command:

    python score.py \
      --parent_id <Synapse ID to log folder> \
      -s <filepath to Synapse configuration file, .synapseConfig> \
      -c <filepath to CaPTk application> \
      -g <filepath to tarball/zipped archive of ground truth> \
      -p <filepath to tarball/zipped archive of predictions>

Two output files are produced, `results.json` and `scores.csv`, where:

- `results.json` is a JSON file containing metric averages across all
  scored predictions
- `scores.csv` is a CSV file containing individual metric scores

## Running with Docker

_TODO_

<!-- Links -->

[`validation-phase-workflow.cwl`]: https://raw.githubusercontent.com/Sage-Bionetworks-Challenges/brats-dream-challenge-infra/main/validation-phase-workflow.cwl
[`testing-phase-workflow.cwl`]: https://raw.githubusercontent.com/Sage-Bionetworks-Challenges/brats-dream-challenge-infra/main/testing-phase-workflow.cwl
[captk]: https://cbica.github.io/CaPTk/
[synapse platform]: https://www.synapse.org/
[captk 1.8.1+]: https://cbica.github.io/CaPTk/Download.html
[evaluation container]: https://www.synapse.org/#!Synapse:syn27788111
[docker]: https://docs.docker.com/get-docker/
