#!/usr/bin/env cwl-runner
#
# Score submission file
#
cwlVersion: v1.0
class: CommandLineTool
baseCommand: score.py

hints:
  DockerRequirement:
    dockerPull: docker.synapse.org/syn25829070/scoring:v4

inputs:
  - id: parent_id
    type: string
  - id: synapse_config
    type: File
  - id: scores
    type: Directory
  - id: check_validation_finished
    type: boolean?

arguments:
  - valueFrom: $(inputs.parent_id)
    prefix: --parent_id
  - valueFrom: $(inputs.synapse_config.path)
    prefix: -s
  - valueFrom: results.json
    prefix: -o

requirements:
  - class: InlineJavascriptRequirement
  - class: InitialWorkDirRequirement
     
outputs:
  - id: results
    type: File
    outputBinding:
      glob: results.json

  - id: status
    type: string
    outputBinding:
      glob: results.json
      loadContents: true
      outputEval: $(JSON.parse(self[0].contents)['submission_status'])