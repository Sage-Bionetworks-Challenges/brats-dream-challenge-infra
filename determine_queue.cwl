#!/usr/bin/env cwl-runner
#
# Extract the submitted Docker repository and Docker digest
#
cwlVersion: v1.0
class: CommandLineTool
baseCommand: python3

hints:
  DockerRequirement:
    dockerPull: sagebionetworks/synapsepythonclient:v2.4.0

inputs:
  - id: synapse_config
    type: File

arguments:
  - valueFrom: determine_queue.py
  - valueFrom: $(inputs.synapse_config.path)
    prefix: -c

requirements:
  - class: InlineJavascriptRequirement
  - class: InitialWorkDirRequirement
    listing:
      - entryname: determine_queue.py
        entry: |
          #!/usr/bin/env python
          import synapseclient
          import argparse
          import json
          import os
          parser = argparse.ArgumentParser()
          parser.add_argument("-c", "--synapse_config", required=True, help="credentials file")
          args = parser.parse_args()
          syn = synapseclient.Synapse(configPath=args.synapse_config)
          syn.login()
          # query submission view and determine which internal queue
          # to submit to
          #sub = syn.tableQuery(args.submissionid)

          evaluation_dict = {"submit_to": "9614875"}
          with open("results.json", 'w') as json_file:
            json_file.write(json.dumps(evaluation_dict))

outputs:
  - id: submit_to_queue
    type: string
    outputBinding:
      glob: results.json
      loadContents: true
      outputEval: $(JSON.parse(self[0].contents)['submit_to'])

  - id: results
    type: File
    outputBinding:
      glob: results.json
