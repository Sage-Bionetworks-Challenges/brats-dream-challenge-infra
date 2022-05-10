#!/usr/bin/env cwl-runner
#
# This tool can be used to create extra submission annotations
# Add inputs and update_status.json to create a JSON to annotate submissions
#

cwlVersion: v1.0
class: CommandLineTool
baseCommand: echo  # Needs a basecommand, so use echo as a hack

inputs:

  - id: admin_synid
    type: string

requirements:
  InlineJavascriptRequirement: {}
  InitialWorkDirRequirement:
    listing:
      - entryname: update_status.json
        entry: |
          {"admin_folder": \"$(inputs.admin_synid)\"}

outputs:
  - id: json_out
    type: File
    outputBinding:
      glob: update_status.json
