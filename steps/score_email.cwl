#!/usr/bin/env cwl-runner

cwlVersion: v1.0
class: CommandLineTool

requirements:
- class: InlineJavascriptRequirement
- class: InitialWorkDirRequirement
  listing:
  - entryname: score_email.py
    entry: |
      #!/usr/bin/env python
      import synapseclient
      import argparse
      import json
      import os
      parser = argparse.ArgumentParser()
      parser.add_argument("-s", "--submissionid", required=True, help="Submission ID")
      parser.add_argument("-c", "--synapse_config", required=True, help="credentials file")
      parser.add_argument("-r", "--results", required=True, help="Resulting scores")
      parser.add_argument("-p", "--private_annotations", nargs="+", default=[], help="annotations to not be sent via e-mail")

      args = parser.parse_args()
      syn = synapseclient.Synapse(configPath=args.synapse_config)
      syn.login()

      sub = syn.getSubmission(args.submissionid)
      participantid = sub.get("teamId")
      if participantid is not None:
        name = syn.getTeam(participantid)['name']
      else:
        participantid = sub.userId
        name = syn.getUserProfile(participantid)['userName']
      evaluation = syn.getEvaluation(sub.evaluationId)
      with open(args.results) as json_data:
        annots = json.load(json_data)
      if annots.get('submission_status') is None:
        raise Exception("score.cwl must return submission_status as a json key")
      status = annots['submission_status']
      if status == "SCORED":
          csv_id = annots['submission_scores']
          del annots['submission_status']
          del annots['submission_scores']
          subject = "Submission to '%s' scored!" % evaluation.name
          for annot in args.private_annotations:
            del annots[annot]
          if len(annots) == 0:
              message = "Your submission has been scored. Results will be announced at a later time."
          else:
              message = ["Hello %s,\n\n" % name,
                         "Your submission (id: %s) has been scored and below are the metric averages:\n\n" % sub.id,
                         "\n".join([i + " : " + str(annots[i]) for i in annots]),
                         "\n\n",
                         "To look at each scan's score, go here: https://www.synapse.org/#!Synapse:%s" % csv_id,
                         "\n\n",
                         "<h3>⚠️ IMPORTANT!!! Starting BraTS 2023, the <u>label value for ET will be '3'</u> (not '4').</h3>",
                         "If you are planning to participate in BraTS 2023, we kindly ask that you be cognizant of ",
                         "this change and update your algorithms as needed to reflect this change.\nFor more details, go to ",
                         "<a href='https://www.synapse.org/#!Synapse:syn51156910/wiki/622351'>BraTS 2023</a>."
                         "\n\nSincerely,\nChallenge Administrator"]
          syn.sendMessage(
              userIds=[participantid],
              messageSubject=subject,
              messageBody="".join(message))

inputs:
- id: submissionid
  type: int
- id: synapse_config
  type: File
- id: results
  type: File
- id: private_annotations
  type: string[]?

outputs:
- id: finished
  type: boolean
  outputBinding:
    outputEval: $( true )

baseCommand: python3
arguments:
- valueFrom: score_email.py
- prefix: -s
  valueFrom: $(inputs.submissionid)
- prefix: -c
  valueFrom: $(inputs.synapse_config.path)
- prefix: -r
  valueFrom: $(inputs.results)
- prefix: -p
  valueFrom: $(inputs.private_annotations)

hints:
  DockerRequirement:
    dockerPull: sagebionetworks/synapsepythonclient:v2.4.0
