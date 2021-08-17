#!/usr/bin/env cwl-runner
#
# Internal workflow.  Runs on UW data
#
# Inputs:
#   submissionId: ID of the Synapse submission to process
#   adminUploadSynId: ID of a folder accessible only to the submission queue administrator
#   submitterUploadSynId: ID of a folder accessible to the submitter
#   workflowSynapseId:  ID of the Synapse entity containing a reference to the workflow file(s)
#
cwlVersion: v1.0
class: Workflow

requirements:
  - class: StepInputExpressionRequirement

inputs:
  - id: submissionId
    type: int
  - id: adminUploadSynId
    type: string
  - id: submitterUploadSynId
    type: string
  - id: workflowSynapseId
    type: string
  - id: synapseConfig
    type: File

# there are no output at the workflow engine level.  Everything is uploaded to Synapse
outputs: []

steps:

  set_submitter_folder_permissions:
    run: https://raw.githubusercontent.com/Sage-Bionetworks/ChallengeWorkflowTemplates/v3.2/cwl/set_permissions.cwl
    in:
      - id: entityid
        source: "#submitterUploadSynId"
      - id: principalid
        valueFrom: "3427583"
      - id: permissions
        valueFrom: "download"
      - id: synapse_config
        source: "#synapseConfig"
    out: []

  get_submissionid:
    run: get_linked_submissionid.cwl
    in:
      - id: submissionid
        source: "#submissionId"
      - id: synapse_config
        source: "#synapseConfig"
    out:
      - id: submissionid
      - id: evaluation_id
      - id: results

  annotate_internal_submission:
    run: https://raw.githubusercontent.com/Sage-Bionetworks/ChallengeWorkflowTemplates/v3.2/cwl/annotate_submission.cwl
    in:
      - id: submissionid
        source: "#submissionId"
      - id: annotation_values
        source: "#get_evaluation_config/config"
      - id: to_public
        default: true
      - id: force
        default: true
      - id: synapse_config
        source: "#synapseConfig"
    out: [finished]

  download_goldstandard:
    run: https://raw.githubusercontent.com/Sage-Bionetworks-Workflows/dockstore-tool-synapse/v0.2/cwl/synapse-get-tool.cwl
    in:
      - id: synapseid
        valueFrom: "syn26017031"
      - id: synapse_config
        source: "#synapseConfig"
    out:
      - id: filepath

  get_docker_config:
    run: https://raw.githubusercontent.com/Sage-Bionetworks/ChallengeWorkflowTemplates/v3.2/cwl/get_docker_config.cwl
    in:
      - id: synapse_config
        source: "#synapseConfig"
    out: 
      - id: docker_registry
      - id: docker_authentication

  get_docker_submission:
    run: get_submission_docker.cwl
    in:
      - id: submissionid
        source: "#get_submissionid/submissionid"
      - id: synapse_config
        source: "#synapseConfig"
    out:
      - id: docker_repository
      - id: docker_digest
      - id: entity_id
      - id: results
      - id: admin_synid
      - id: submitter_synid

  annotate_submission_main_submitter:
    run: https://raw.githubusercontent.com/Sage-Bionetworks/ChallengeWorkflowTemplates/v3.2/cwl/annotate_submission.cwl
    in:
      - id: submissionid
        source: "#submissionId"
      - id: annotation_values
        source: "#get_docker_submission/results"
      - id: to_public
        default: true
      - id: force
        default: true
      - id: synapse_config
        source: "#synapseConfig"
    out: [finished]

  run_docker:
    run: run_docker.cwl
    in:
      - id: docker_repository
        source: "#get_docker_submission/docker_repository"
      - id: docker_digest
        source: "#get_docker_submission/docker_digest"
      - id: submissionid
        source: "#submissionId"
      - id: docker_registry
        source: "#get_docker_config/docker_registry"
        # valueFrom: "docker.synapse.org"
      - id: docker_authentication
        source: "#get_docker_config/docker_authentication"
      - id: parentid
        source: "#submitterUploadSynId"
      - id: synapse_config
        source: "#synapseConfig"
      - id: input_dir
        source: "#get_evaluation_config/dataset_path"
      - id: docker_script
        default:
          class: File
          location: "run_docker.py"
      - id: quota
        source: "#get_evaluation_config/runtime"
    out:
      - id: predictions

  validate:
    run: validate.cwl
    in:
      - id: input_file
        source: "#download_submission/filepath"
      - id: goldstandard
        source: "#download_goldstandard/filepath"
      - id: entity_type
        source: "#download_submission/entity_type"
    out:
      - id: results
      - id: status
      - id: invalid_reasons
      - id: predictions
      - id: references
  
  email_validation:
    run: https://raw.githubusercontent.com/Sage-Bionetworks/ChallengeWorkflowTemplates/v3.2/cwl/validate_email.cwl
    in:
      - id: submissionid
        source: "#get_submissionid/submissionid"
      - id: synapse_config
        source: "#synapseConfig"
      - id: status
        source: "#validate/status"
      - id: invalid_reasons
        source: "#validate/invalid_reasons"
      - id: errors_only
        default: true
    out: [finished]

  annotate_main_submission_with_validation:
    run: https://raw.githubusercontent.com/Sage-Bionetworks/ChallengeWorkflowTemplates/v3.2/cwl/annotate_submission.cwl
    in:
      - id: submissionid
        source: "#get_submissionid/submissionid"
      - id: annotation_values
        source: "#validate/results"
      - id: to_public
        default: true
      - id: force
        default: true
      - id: synapse_config
        source: "#synapseConfig"
    out: [finished]

  annotate_submission_with_validation:
    run: https://raw.githubusercontent.com/Sage-Bionetworks/ChallengeWorkflowTemplates/v3.2/cwl/annotate_submission.cwl
    in:
      - id: submissionid
        source: "#submissionId"
      - id: annotation_values
        source: "#validate/results"
      - id: to_public
        default: true
      - id: force
        default: true
      - id: synapse_config
        source: "#synapseConfig"
    out: [finished]

  check_status:
    run: https://raw.githubusercontent.com/Sage-Bionetworks/ChallengeWorkflowTemplates/v3.2/cwl/check_status.cwl
    in:
      - id: status
        source: "#validate/status"
      - id: previous_annotation_finished
        source: "#annotate_main_submission_with_validation/finished"
      - id: previous_email_finished
        source: "#email_validation/finished"
    out: [finished]

  score:
    run: score.cwl
    in:
      - id: parent_id
        source: "#submitterUploadSynId"
      - id: synapse_config
        source: "#synapseConfig"
      - id: input_file
        source: "#download_submission/filepath"
      - id: goldstandard
        source: "#download_goldstandard/filepath"
      - id: check_validation_finished
        source: "#check_status/finished"
    out:
      - id: results
      - id: status

  email_score:
    run: https://raw.githubusercontent.com/Sage-Bionetworks/ChallengeWorkflowTemplates/v3.2/cwl/score_email.cwl
    in:
      - id: submissionid
        source: "#get_submissionid/submissionid"
      - id: synapse_config
        source: "#synapseConfig"
      - id: results
        source: "#score/scores"
    out: []

  annotate_main_submission_with_scores:
    run: https://raw.githubusercontent.com/Sage-Bionetworks/ChallengeWorkflowTemplates/v3.2/cwl/annotate_submission.cwl
    in:
      - id: submissionid
        source: "#get_submissionid/submissionid"
      - id: annotation_values
        source: "#score/results"
      - id: to_public
        default: true
      - id: force
        default: true
      - id: synapse_config
        source: "#synapseConfig"
    out: [finished]

  # annotate internal submission with scores
  annotate_submission_with_scores:
    run: https://raw.githubusercontent.com/Sage-Bionetworks/ChallengeWorkflowTemplates/v3.2/cwl/annotate_submission.cwl
    in:
      - id: submissionid
        source: "#submissionId"
      - id: annotation_values
        source: "#score/results"
      - id: to_public
        default: true
      - id: force
        default: true
      - id: synapse_config
        source: "#synapseConfig"
    out: [finished]
 