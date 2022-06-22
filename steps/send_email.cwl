#!/usr/bin/env cwl-runner

cwlVersion: v1.0
class: CommandLineTool

requirements:
- class: InlineJavascriptRequirement
- class: InitialWorkDirRequirement
  listing:
  - entryname: send_model_files.py
    entry: |
      #!/usr/bin/env python
      import synapseclient
      import argparse
      import json
      import os

      parser = argparse.ArgumentParser()
      parser.add_argument("-s", "--submissionid", required=True, help="Submission ID")
      parser.add_argument("-c", "--synapse_config", required=True, help="credentials file")
      parser.add_argument("-r", "--model", required=True, help="Zipped model files")
      parser.add_argument("-p", "--parentid", required=True, help="Parent ID to upload file")
      args = parser.parse_args()

      syn = synapseclient.Synapse(configPath=args.synapse_config)
      syn.login()
      model_zip = synapseclient.File(args.model, parent=args.parentid)
      model_zip = syn.store(model_zip)
      zip_id = model_zip.id

      sub = syn.getSubmission(args.submissionid)
      participantid = sub.get("teamId")
      if participantid is not None:
        name = syn.getTeam(participantid)['name']
      else:
        participantid = sub.userId
        name = syn.getUserProfile(participantid)['userName']
      evaluation = syn.getEvaluation(sub.evaluationId)
      subject = "'%s' - Model Training Complete" % evaluation.name
      message = ["Hello %s,\n\n" % name,
                 "Congrats! Your submission (id: %s) has finished training.\n\n" % sub.id,
                 "To access your model files, go here: https://www.synapse.org/#!Synapse:%s" %zip_id,
                 "\n\nSincerely,\nBraTS Challenge Organizers"]
      syn.sendMessage(
          userIds=[participantid],
          messageSubject=subject,
          messageBody="".join(message))

inputs:
- id: submissionid
  type: int
- id: synapse_config
  type: File
- id: model
  type: File
- id: parentid
  type: string

outputs:
- id: finished
  type: boolean
  outputBinding:
    outputEval: $( true )

baseCommand: python3
arguments:
- valueFrom: send_model_files.py
- prefix: -s
  valueFrom: $(inputs.submissionid)
- prefix: -c
  valueFrom: $(inputs.synapse_config.path)
- prefix: -r
  valueFrom: $(inputs.model.path)
- prefix: -p
  valueFrom: $(inputs.parentid)

hints:
  DockerRequirement:
    dockerPull: sagebionetworks/synapsepythonclient:v2.4.0
