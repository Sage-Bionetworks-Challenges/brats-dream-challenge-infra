#!/usr/bin/env cwl-runner
#
# Score submission file
#
cwlVersion: v1.0
class: CommandLineTool
baseCommand: sh

inputs:
  - id: script
    type: File
    inputBinding:
      position: 0
  - id: predictions
    type: Directory
  - id: goldstandard
    type: Directory

requirements:
  #- class: InlineJavascriptRequirement
  InitialWorkDirRequirement:
    listing:
      - $(inputs.predictions)
      - $(inputs.goldstandard)
     
outputs:
  - id: scores
    type: File
    outputBinding:
      glob: "inFileList.csv"

  - id: errors
    type: File
    outputBinding:
      glob: "invalid_input_data.csv"
