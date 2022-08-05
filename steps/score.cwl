#!/usr/bin/env cwl-runner
#
# Score submission file
#
cwlVersion: v1.0
class: CommandLineTool
baseCommand: score.py

hints:
  DockerRequirement:
    dockerPull: docker.synapse.org/syn27046445/scoring:test-phase

inputs:
  - id: parent_id
    type: string
  - id: synapse_config
    type: File
  - id: input_file
    type: File
  - id: goldstandard
    type: File
  - id: dataset
    type: string
  - id: check_validation_finished
    type: boolean?

arguments:
  - valueFrom: $(inputs.parent_id)
    prefix: --parent_id
  - valueFrom: $(inputs.synapse_config.path)
    prefix: -s
  - valueFrom: $(inputs.input_file.path)
    prefix: -p
  - valueFrom: $(inputs.goldstandard.path)
    prefix: -g
  - valueFrom: $(inputs.dataset)
    prefix: -d
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

  - id: status
    type: string
    outputBinding:
      glob: results.json
      loadContents: true
      outputEval: $(JSON.parse(self[0].contents)['submission_status'])