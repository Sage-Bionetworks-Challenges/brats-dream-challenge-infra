#!/usr/bin/env cwl-runner
#
# Submissions from certain user IDs will automatically CLOSE,
# due to circumventing the submission limits.

cwlVersion: v1.0
class: CommandLineTool
baseCommand: python3

hints:
  DockerRequirement:
    dockerPull: sagebionetworks/synapsepythonclient:v2.4.0

inputs:
  - id: submissionid
    type: int
  - id: synapse_config
    type: File
  - id: blacklist_ids
    type: int[]

arguments:
  - valueFrom: check_submitter_id.py
  - valueFrom: $(inputs.submissionid)
    prefix: -s
  - valueFrom: $(inputs.synapse_config.path)
    prefix: -c
  - valueFrom: $(inputs.blacklist_ids)
    prefix: -b


requirements:
  - class: InlineJavascriptRequirement
  - class: InitialWorkDirRequirement
    listing:
      - entryname: check_submitter_id.py
        entry: |
          #!/usr/bin/env python
          import synapseclient
          import argparse

          parser = argparse.ArgumentParser()
          parser.add_argument("-s", "--submissionid", required=True, help="Submission ID")
          parser.add_argument("-c", "--synapse_config", required=True, help="credentials file")
          parser.add_argument("-b", "--blacklist", nargs="+", default=[], help="list of blacklisted IDs")

          args = parser.parse_args()
          syn = synapseclient.Synapse(configPath=args.synapse_config)
          syn.login()

          sub = syn.getSubmission(args.submissionid, downloadFile=False)
          submitterid = sub.get('teamId', sub.get('userId'))
          if int(submitterid) in args.blacklist:
            sub_status = syn.getSubmissionStatus(args.submissionid)
            sub_status.status = "CLOSED"
            syn.store(sub_status)
            raise Exception("invalid submission")
          
outputs:
- id: finished
  type: boolean
  outputBinding:
    outputEval: $( true )