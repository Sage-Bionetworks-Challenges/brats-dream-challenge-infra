# RSNA-ASNR-MICCAI BraTS Challenge 2021

For this challenge, two workflows are needed:

- `validation-phase-workflow.cwl`, which will accept a single predictions file and score it against the ground truth file, using CaPTK 1.8.1

- `testing-phase-workflow.cwl`, which will accept a Docker model to first infer the predictions, and then scoring them with CaPTK 1.8.1

Metrics returned will be the "Dice SImilarity Coefficient" and the "Hausdorff distance (95%)", as well as the sensitivity and specificity.

## Adding internal GPU instances

1. Create evaluation queue (BraTS Challenge Internal Queue N) -> Provide admin access to thomas.yu, vchung, dream_service
2. Create instance from `brats-gpu-ami `AMI
3. ssh into new instance and update the .env template to the queue id (Each instance should only be linked to one queue)
4. Add queue to internal queue submission view: https://www.synapse.org/#!Synapse:syn26125000/tables/
5. Start the orchestrator in the GPU server!
