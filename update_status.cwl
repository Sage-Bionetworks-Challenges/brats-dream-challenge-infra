#!/usr/bin/env cwl-runner
#
# Annotate an existing submission status
#

cwlVersion: v1.0
class: CommandLineTool
baseCommand: challengeutils

hints:
  DockerRequirement:
    dockerPull: sagebionetworks/challengeutils:v4.1.0

requirements:
  - class: InlineJavascriptRequirement

inputs:
  - id: submissionid
    type: int
  - id: status
    type: string
  - id: synapse_config
    type: File

arguments:
  - valueFrom: $(inputs.synapse_config.path)
    prefix: -c
  - valueFrom: change-status
  - valueFrom: $(inputs.submissionid)
  - valueFrom: $(inputs.status)

outputs:
- id: finished
  type: boolean
  outputBinding:
    outputEval: $( true )