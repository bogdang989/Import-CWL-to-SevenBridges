class: CommandLineTool
cwlVersion: v1.0
id: cwl_to_cgc_cwl
baseCommand: []
inputs:
  - type: File
    id: cwl
    label: Standalone cwl workflow
    doc: Standalone CWL workflow file.
    secondaryFiles: []
  - type: string
    id: token
    inputBinding:
      position: 3
      prefix: '--token'
      shellQuote: false
    label: Developer token
    doc: >-
      Your authentication token for the required platfrom. It can be found in
      the developer tab.
      (http://docs.sevenbridges.com/docs/get-your-authentication-token)
    secondaryFiles: []
  - type: string
    id: project_id
    inputBinding:
      position: 4
      prefix: '--project_id'
      shellQuote: false
    label: Project id
    doc: >-
      Project id is collected from project main page url. Format:
      (user-name/project-name)
    secondaryFiles: []
  - type: File?
    id: cwl_inputs
    inputBinding:
      position: 5
      prefix: '--cwl-inputs'
      shellQuote: false
    label: CWL Inputs
    doc: >-
      If CWL inputs file is provided, all files required for task execution
      shall be uploaded to the platform and a draft task shall be created.
    secondaryFiles: []
  - type: boolean?
    id: run_task
    inputBinding:
      position: 8
      prefix: '--run-task'
    label: Run task
    doc: >-
      If true and cwl_inputs file is provided, execution of the draft task will
      be initiated.
    secondaryFiles: []
  - type: string?
    id: aws_instance_type
    inputBinding:
      position: 9
      prefix: '--aws-instance-type'
    label: AWS instance type
    doc: >-
      Select EC2 instance type for task execution.
      (http://www.ec2instances.info/ select one from the column API Name)
    secondaryFiles: []
outputs: []
label: cwl_to_cgc
arguments:
  - position: 0
    shellQuote: false
    valueFrom: |-
      ${
          var standalone = inputs.cwl.nameroot + '-standalone.json';
          return '$BUNNY -r ' + inputs.cwl.path + ' > ' + standalone + ' && python3 /opt/import_cwl_to_sbg.py --cwl ' + standalone
      }
requirements:
  - class: ShellCommandRequirement
  - class: InlineJavascriptRequirement
  - class: DockerRequirement
    dockerPull: 'images.sbgenomics.com/bogdang/cwl_to_sbg:1.0'