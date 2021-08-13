#!/usr/bin/env cwl-runner
#
# Score submission file
#
cwlVersion: v1.0
class: CommandLineTool
baseCommand: score.sh

# hints:
#   DockerRequirement:
#     dockerPull: docker.synapse.org/syn25829070/scoring:v4

inputs:
  - id: predictions
    type: Directory
  - id: goldstandard
    type: Directory
  - id: captk
    type: Directory

requirements:
  #- class: InlineJavascriptRequirement
  InitialWorkDirRequirement:
    listing:
      - $(inputs.predictions)
      - $(inputs.goldstandard)
      - $(inputs.captk)
     
outputs:
  - id: scores
    type: Directory
    outputBinding:
      glob: "scores"

  - id: errors
    type: File
    outputBinding:
      glob: "invalid_input_data.csv"
