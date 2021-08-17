#!/usr/bin/env cwl-runner
#
# Main workflow.  Runs through synthetic data and submits to internal queues
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
  - class: ScatterFeatureRequirement

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
  create_adminsynid_json:
    run: create_annotations.cwl
    in:
      - id: admin_synid
        source: "#adminUploadSynId"
    out: [json_out]

  annotate_adminsynid:
    run: https://raw.githubusercontent.com/Sage-Bionetworks/ChallengeWorkflowTemplates/v3.2/cwl/annotate_submission.cwl
    in:
      - id: submissionid
        source: "#submissionId"
      - id: annotation_values
        source: "#create_adminsynid_json/json_out"
      - id: to_public
        default: true
      - id: force_change_annotation_acl
        default: true
      - id: synapse_config
        source: "#synapseConfig"
    out: [finished]

  # Give download permission to challenge organizing team
  set_submitter_folder_permissions:
    run:  https://raw.githubusercontent.com/Sage-Bionetworks/ChallengeWorkflowTemplates/v3.2/cwl/set_permissions.cwl
    in:
      - id: entityid
        source: "#adminUploadSynId"
      - id: principalid
        valueFrom: "3427583"  # Change this
      - id: permissions
        valueFrom: "download"
      - id: synapse_config
        source: "#synapseConfig"
    out: []

  # Give download permission to challenge organizing team
  set_admin_folder_permissions:
    run:  https://raw.githubusercontent.com/Sage-Bionetworks/ChallengeWorkflowTemplates/v3.2/cwl/set_permissions.cwl
    in:
      - id: entityid
        source: "#submitterUploadSynId"
      - id: principalid
        valueFrom: "3427583"  # Change this
      - id: permissions
        valueFrom: "download"
      - id: synapse_config
        source: "#synapseConfig"
    out: []

  get_docker_submission:
    run: https://raw.githubusercontent.com/Sage-Bionetworks/ChallengeWorkflowTemplates/v3.2/cwl/get_submission.cwl
    in:
      - id: submissionid
        source: "#submissionId"
      - id: synapse_config
        source: "#synapseConfig"
    out:
      - id: filepath
      - id: docker_repository
      - id: docker_digest
      - id: entity_id
      - id: entity_type
      - id: evaluation_id
      - id: results

  download_goldstandard:
    run: https://raw.githubusercontent.com/Sage-Bionetworks-Workflows/dockstore-tool-synapse/v1.3/cwl/synapse-get-tool.cwl
    in:
      - id: synapseid
        valueFrom: "syn26017031"
      - id: synapse_config
        source: "#synapseConfig"
    out:
      - id: filepath

  validate_docker:
    run: https://raw.githubusercontent.com/Sage-Bionetworks/ChallengeWorkflowTemplates/v3.2/cwl/validate_docker.cwl
    in:
      - id: submissionid
        source: "#submissionId"
      - id: synapse_config
        source: "#synapseConfig"
    out:
      - id: results
      - id: status
      - id: invalid_reasons

  annotate_docker_validation_with_output:
    run: https://raw.githubusercontent.com/Sage-Bionetworks/ChallengeWorkflowTemplates/v3.2/cwl/annotate_submission.cwl
    in:
      - id: submissionid
        source: "#submissionId"
      - id: annotation_values
        source: "#validate_docker/results"
      - id: to_public
        default: true
      - id: force
        default: true
      - id: synapse_config
        source: "#synapseConfig"
    out: [finished]

  email_docker_validation:
    run: https://raw.githubusercontent.com/Sage-Bionetworks/ChallengeWorkflowTemplates/v3.2/cwl/validate_email.cwl
    in:
      - id: submissionid
        source: "#submissionId"
      - id: synapse_config
        source: "#synapseConfig"
      - id: status
        source: "#validate_docker/status"
      - id: invalid_reasons
        source: "#validate_docker/invalid_reasons"
      - id: errors_only
        default: true
    out: [finished]

  check_docker_status:
    run: https://raw.githubusercontent.com/Sage-Bionetworks/ChallengeWorkflowTemplates/v3.2/cwl/check_status.cwl
    in:
      - id: status
        source: "#validate_docker/status"
      - id: previous_annotation_finished
        source: "#annotate_docker_validation_with_output/finished"
      - id: previous_email_finished
        source: "#email_docker_validation/finished"
    out: [finished]

  get_docker_config:
    run: https://raw.githubusercontent.com/Sage-Bionetworks/ChallengeWorkflowTemplates/v3.2/cwl/get_docker_config.cwl
    in:
      - id: synapse_config
        source: "#synapseConfig"
    out: 
      - id: docker_registry
      - id: docker_authentication

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
      - id: previous
        source: "#check_docker_status/finished"
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
      #- id: quota
      #  source: "#get_evaluation_config/runtime"
    out:
      - id: predictions

  upload_results:
    run: https://raw.githubusercontent.com/Sage-Bionetworks/ChallengeWorkflowTemplates/v3.2/cwl/upload_to_synapse.cwl
    in:
      - id: infile
        source: "#run_docker/predictions"
      - id: parentid
        source: "#adminUploadSynId"
      - id: used_entity
        source: "#get_docker_submission/entity_id"
      - id: executed_entity
        source: "#workflowSynapseId"
      - id: synapse_config
        source: "#synapseConfig"
    out:
      - id: uploaded_fileid
      - id: uploaded_file_version
      - id: results

  annotate_docker_upload_results:
    run: https://raw.githubusercontent.com/Sage-Bionetworks/ChallengeWorkflowTemplates/v3.2/cwl/annotate_submission.cwl
    in:
      - id: submissionid
        source: "#submissionId"
      - id: annotation_values
        source: "#upload_results/results"
      - id: to_public
        default: true
      - id: force
        default: true
      - id: synapse_config
        source: "#synapseConfig"
    out: [finished]

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
        source: "#submissionId"
      - id: synapse_config
        source: "#synapseConfig"
      - id: status
        source: "#validate/status"
      - id: invalid_reasons
        source: "#validate/invalid_reasons"
      - id: errors_only
        default: true
    out: [finished]

  annotate_validation_with_output:
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
        source: "#annotate_validation_with_output/finished"
      - id: previous_email_finished
        source: "#email_validation/finished"
    out: [finished]

  create_submission_file:
    run: create_submission_file.cwl
    in:
      - id: submissionid
        source: "#submissionId"
      # Just needs to be a previous boolean step
      - id: previous
        source: "#check_status/finished"
    out: [submission_out]

  upload_submission_file:
    run: https://raw.githubusercontent.com/Sage-Bionetworks/ChallengeWorkflowTemplates/v3.2/cwl/upload_to_synapse.cwl
    in:
      - id: infile
        source: "#create_submission_file/submission_out"
      - id: parentid
        source: "#adminUploadSynId"
      - id: used_entity
        source: "#get_docker_submission/entity_id"
      - id: executed_entity
        source: "#workflowSynapseId"
      - id: synapse_config
        source: "#synapseConfig"
    out:
      - id: uploaded_fileid
      - id: uploaded_file_version
      - id: results

  # Add tool to determine which queue to submit to
  determine_internal_queue:
    run: determine_queue.cwl
    in:
      - id: synapse_config
        source: "#synapseConfig"
    out:
      - id: submit_to_queue

  # Ability to submit to many internal queues
  submit_to_internal_queues:
    run: https://raw.githubusercontent.com/Sage-Bionetworks/ChallengeWorkflowTemplates/v3.2/cwl/submit_to_challenge.cwl
    scatter: evaluationid
    in:
      - id: submission_file
        source: "#upload_submission_file/uploaded_fileid"
      - id: submissionid
        source: "#submissionId"
      - id: synapse_config
        source: "#synapseConfig"
      - id: evaluationid
        source: "#determine_internal_queue/submit_to_queue"
    out: []
