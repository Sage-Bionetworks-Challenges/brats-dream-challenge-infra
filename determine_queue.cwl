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
          import argparse
          import json
          import os
          import random

          import pandas as pd
          import synapseclient

          parser = argparse.ArgumentParser()
          parser.add_argument("-c", "--synapse_config", required=True, help="credentials file")
          args = parser.parse_args()
          syn = synapseclient.Synapse(configPath=args.synapse_config)
          syn.login()
          view_ent = syn.get("syn26125000")
          scope_ids = pd.Series(view_ent.scopeIds).astype(int)
          # Do a quick query to make sure most up to date view
          syn.tableQuery("select * from syn26125000 limit 1")
          # query submission view and determine which internal queue
          # to submit to
          sub_count = syn.tableQuery("SELECT evaluationid, count(*) as num FROM syn26125000  where status in ('RECEIVED','EVALUATION_IN_PROGRESS') group by evaluationid")
          sub_count_df = sub_count.asDataFrame()
          running_queues = scope_ids.isin(sub_count_df['evaluationid'])
          if all(running_queues):
            sub_count_df = sub_count_df.sort_values('num')
            submit_to = sub_count_df['evaluationid'].iloc[0]
          else:
            # Randomly choose queue that might be empty
            submit_to = scope_ids[~running_queues].sample().iloc[0]

          evaluation_dict = {"submit_to": str(submit_to)}
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
