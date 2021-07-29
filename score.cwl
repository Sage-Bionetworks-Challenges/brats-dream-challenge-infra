#!/usr/bin/env cwl-runner
#
# Score submission file
#
cwlVersion: v1.0
class: CommandLineTool
baseCommand: score.py

hints:
  DockerRequirement:
    dockerPull: docker.synapse.org/syn25829070/scoring:v2

inputs:
  - id: parent_id
    type: string
  - id: synapse_config
    type: string
  - id: input_file
    type: File
  - id: goldstandard
    type: File
  - id: check_validation_finished
    type: boolean?

arguments:
  - valueFrom: $(inputs.parent_id)
    prefix: --parentid
  - valueFrom: $(inputs.synapse_config.path)
    prefix: -c
  - valueFrom: $(inputs.input_file.path)
    prefix: -p
  - valueFrom: $(inputs.goldstandard.path)
    prefix: -g
  - valueFrom: "/work/CaPTk"
    prefix: -c
  - valueFrom: results.json
    prefix: -o

requirements:
  - class: InlineJavascriptRequirement
     
outputs:
  - id: results
    type: File
    outputBinding:
      glob: results.json

  - id: Dice_ET
    type:
      - string
      - float
    outputBinding:
      glob: results.json
      loadContents: true
      outputEval: $(JSON.parse(self[0].contents)['Dice_ET'])

  - id: Dice_WT
    type:
      - string
      - float
    outputBinding:
      glob: results.json
      loadContents: true
      outputEval: $(JSON.parse(self[0].contents)['Dice_WT'])

  - id: Dice_TC
    type:
      - string
      - float
    outputBinding:
      glob: results.json
      loadContents: true
      outputEval: $(JSON.parse(self[0].contents)['Dice_TC'])

  - id: Hausdorff95_ET
    type:
      - string
      - float
    outputBinding:
      glob: results.json
      loadContents: true
      outputEval: $(JSON.parse(self[0].contents)['Hausdorff95_ET'])

  - id: Hausdorff95_WT
    type:
      - string
      - float
    outputBinding:
      glob: results.json
      loadContents: true
      outputEval: $(JSON.parse(self[0].contents)['Hausdorff95_WT'])

  - id: Hausdorff95_TC
    type:
      - string
      - float
    outputBinding:
      glob: results.json
      loadContents: true
      outputEval: $(JSON.parse(self[0].contents)['Hausdorff95_TC'])

  - id: Sensitivity_ET
    type:
      - string
      - float
    outputBinding:
      glob: results.json
      loadContents: true
      outputEval: $(JSON.parse(self[0].contents)['Sensitivity_ET'])

  - id: Sensitivity_WT
    type:
      - string
      - float
    outputBinding:
      glob: results.json
      loadContents: true
      outputEval: $(JSON.parse(self[0].contents)['Sensitivity_WT'])

  - id: Sensitivity_TC
    type:
      - string
      - float
    outputBinding:
      glob: results.json
      loadContents: true
      outputEval: $(JSON.parse(self[0].contents)['Sensitivity_TC'])

  - id: Specificity_ET
    type: float
    outputBinding:
      glob: results.json
      loadContents: true
      outputEval: $(JSON.parse(self[0].contents)['Specificity_ET'])

  - id: Specificity_WT
    type: float
    outputBinding:
      glob: results.json
      loadContents: true
      outputEval: $(JSON.parse(self[0].contents)['Specificity_WT'])

  - id: Specificity_TC
    type: float
    outputBinding:
      glob: results.json
      loadContents: true
      outputEval: $(JSON.parse(self[0].contents)['Specificity_TC'])

  - id: status
    type: string
    outputBinding:
      glob: results.json
      loadContents: true
      outputEval: $(JSON.parse(self[0].contents)['submission_status'])