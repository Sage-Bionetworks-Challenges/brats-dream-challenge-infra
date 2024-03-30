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

<!-- Links -->

[`validation-phase-workflow.cwl`]: https://raw.githubusercontent.com/Sage-Bionetworks-Challenges/brats-dream-challenge-infra/main/validation-phase-workflow.cwl
[`testing-phase-workflow.cwl`]: https://raw.githubusercontent.com/Sage-Bionetworks-Challenges/brats-dream-challenge-infra/main/testing-phase-workflow.cwl
[captk]: https://cbica.github.io/CaPTk/
[synapse platform]: https://www.synapse.org/
[captk 1.8.1+]: https://cbica.github.io/CaPTk/Download.html
[evaluation model]: https://www.synapse.org/#!Synapse:syn27788111
[docker]: https://docs.docker.com/get-docker/
