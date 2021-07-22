# RSNA-ASNR-MICCAI BraTS Challenge 2021

For this challenge, two workflows are needed:

- `validation-phase-workflow.cwl`, which will accept a single predictions file and score it against the ground truth file, using CaPTK 1.8.1

- `testing-phase-workflow.cwl`, which will accept a Docker model to first infer the predictions, and then scoring them with CaPTK 1.8.1

Metrics returned will be the "Dice SImilarity Coefficient" and the "Hausdorff distance (95%)", as well as the sensitivity and specificity.