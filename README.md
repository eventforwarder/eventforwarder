# EventForwarder

EventForwarder is a simple solution for processing and forwarding specific events in AWS. Currently it supports receiving arbitrary events through SNS-topics, it can filter and then process the events through a template based on user defined rules, and then send the processed event to a webhook. It is most useful for delivering events from AWS or othe sources to externa solutions, like Slack or Mattermost, monitoring solutions, etc., where you need to transform multiple different kinds of events to a specific format before forwarding them.

## Deployment

1. Get an AWS account, preferrably one that is dedicated for this use as we will be using ECR repository replication which can only be configured globally for the whole account.
1. Select one main region where you will deploy the single region CloudFormation stacks.
1. Deploy the CloudFormation stack `cfnroles.yaml`. This template creates the required IAM roles for using Stacksets within this account. You may skip this if you have applicable roles already in your account. Name the stack as `Stackset-Roles`.
1. Modify and deploy the ECR replication configuration stack.
    1. The file `ecr-replication-template.yaml` contanis the stack template. Modify this file so that it has only the regions you wish to have the ECR replication enabled.
    1. Deploy the CloudFormation stack with the modified template.
1. Deploy CloudFormation stack `ci.yaml` with defaults if you wish to use the included build pipeline. If you have your own CI pipeline and can push OCI Containers to ECR, you can select not to deploy the build pipeline. This stack will then only create the required ECR repository. Name the stack as `EventForwarder-CI`.
1. Check the outputs for the deployed CI-stack and copy the address for the `CodeCommitRepository`.  
1. Push the EventForwarder repository code fully into the CodeCommit repository shown in the CI-stack output (see instructions below).
1. Check your CodePipline for a successful build. If the build is still running, wait until it is succesfully finished.
1. Deploy CloudFormation stackset `forwarder-stackset.yaml`.
    1. IAM Admin Role Name:  `AWSCloudFormationStackSetAdministrationRole`
    1. IAM Execution Role Name: `AWSCloudFormationStackSetExecutionRole`
    1. Stackset name: `EventForwarder`
    1. You can leave all of the parameters as defaults, except `InputArnsForEventForwarderSQSQueue`. Add your inbound events' SNS Topics arns as comma separated values. See _Using SNS Topics as inputs_.
    1. Account numbers: <_your account number_>
    1. Specify regions: <_the regions where you want to deploy the solution_>
    1. Acknowledge that AWS CloudFormation might create IAM resources.
1. Create your individual CloudFormation template for configuration of EventForwarder. See: _Configuration and Templates_
1. After the Forwarder-stackset has been fully deployed, deploy your configuration template as a stackset to all the regions where EventForwarder was deployed. Use the same single-account deployment as described for the Forwarder-stackset. Name the stackset as `EventForwarder-Config`.
1. After the Config-stackset has been fully deployed to all regions, the deployment should be ready.
1. Subscribe the EventForwarder's Inbound SQS queue to SNS Topics where you have your incoming events. See _Using SNS Topics as inputs_.
1. Verify that the installation works by sending test events to all configured SNS Topics.


### Using SNS Topics as inputs

The `forwarder-stackset.yaml` deployment always creates one SNS Topic for event input on each deployed region. You can find the arn from each stack's output as value `InboundTopic`.

You can also create your own SNS Topics. Remember that these Topics need to exist in **each region** where EventForwarder is deployed to. Add the Topics' arns to the deployment parameter `InputArnsForEventForwarderSQSQueue`. To avoid the need for overrides, use the same name for the Topics in each region, and replace the region in the arn with a wildcard (`*`). Then, subscribe the EventForwarder SQS Queue (Stack output value `InboundQueueArn`) to each topic. 


### Pushing code to the Codecommit repository

The following steps are intended to be executed in CloudShell. If you wish, you can also adapt these commands and run them on any other environment. 

If you choose to run these commands from somewhere else, you will need `awscli` and `git-remote-codecommit` on your client:

```
python3 -m pip install awscli git-remote-codecommit
```

To commit the code, follow these steps:
```
git clone https://.... eventforwarder
cd eventforwarder
git remote add aws <ci-stack-output-CodeCommitRepository>
git push aws
```

### Updating the EventForwarder app for an existing installation 

1. Checkout the version you want to update to from this git repository.
1. Push the new version to the CodeCommit repository.
1. Wait until the container image build is finished.
1. Check the ECR console for the unique image build tag of the latest uploaded container image in the eventvorwarder repository, and copy it. Do not use the latest-tag.
1. Go to the EventForwarder CloudFormation stackset and update it. Set `ContainerVersion` to the tag you copied. Update the stackset.


## Configuration and Templates

EventForwarder configuration data is in json-format and is provided via a single SSM Parameter. You can find the path for this from the Forwarder-stack's output value `ConfigPath`. This SSM Parameter must be in the same region as each EventForwarder instance.

EventForwarder templates are in jinja2-format (with a minor customization) and are provided via an SSM Parameter per template. You can find the path for the template from the Forwarder-stack's output value `TemplatesPath`. This is the root path of each template, for example `/eventforwarder/templates`. Each template will have an SSM Parameter in this path, for example template named `awsalerts` would then have a path `/eventforwarder/templates/awsalerts`. The template SSM Parameters must be in the same region as each EventForwarder instance.

Both Configuration and Templates are highly recommended to be deployed as stacksets to make configuration management as easy as possible. You can use the CloudFormation template file `config-stackset-template.yaml` as a sample template to modify with your own configurations. For your convenience, use the importvalue declarations in the sample template to automatically retrieve the correct SSMP paths for the configuration data and templates.

### Configuration

The configuration is in json-format and must follow the structure shown in the following sample:

```json
{
    "profiles": {
        "default": {
            "endpoint": "<endpoint-url>"
        },
        "awsalerts": {
            "endpoint": "<endpoint-url>",
            "parameters": {
                "channel": "<channel-name>",
                "username": "<users-name>",
                "icon_emoji": "<user-icon-emoji>",
                "text": "@@@@"
            },
            "template": "<template-name>"
        }
    },
    "rules": [
        {
            "rulesets": {
                "Or": [
                    [ "TopicArn", "REGEX", "<sns-topic-name>$" ]
                ]
            },
            "profile": "awsalerts",
            "transform": [
                "json:Message"
            ]
        }
    ]
}
```

There must be `profiles` and `rules` parameters in the root of the json-object. Profiles defines the available profiles that are used for forwarding the events. Rules define the rules which are applied to the incoming messages in order to find our which template should be applied to each event.

### Profiles

The structure of the profiles-propery is as follows:

```json
"profiles": {
    "default": {
        "endpoint": "<endpoint-url>"
    }
    "<profile-1-name>": {
        "endpoint": "<endpoint-url>",
        "parameters": { ... },
        "template": "<template-name>"
    },
    "profile-2-name>": { 
        ...
    }
}
```

The parameters `endpoint` and `template` are required for each profile. The `endpoint`-parameter is the url of the webhook to be called. The `template`-parameter is the name of the template that will be applied for the template processing.

The parameter `parameters` is optional and can be used for providing json-output. Each property in the `parameters`-object will be outputed as such in the resulting json. If one of the parameters has the value of `@@@@`, this parameter will be assigned the output of the template processing. If the `parameters`-parameter is missing, the output will be directly the output of the template processing.

**Note: The default-profile is mandatory.**

### Rules

The structure of the rules-propery is as follows:

```json
"rules": {
    "rulesets": {
        "And|Or": [
            [ ... evaluation rule 1 ... ],
            [ ... evaluation rule 2 ... ],
            ...
            [ ... evaluation rule n ... ]
        ],    
    },
    "profile": "<profile-name-to-apply-if-matched>",
    "transform: [
        "<transform rule 1>",
        "..."
    ]

}
```

The rules are evaluated from top to bottom. When the first rule applies, that profile is used. If no rule matches, the event is discarded. Each rule must have the parameter `rulesets`, and may carry the optional parameters `profile` and `transform`. The `profile`-parameter defines which profile to apply to the event if the `rulesets` match the event. If omitted, the `default` profile will be used.

The `rulesets`-object has either an `Or` or an `And` parameter, that contains an array of evaluation rules to be evaluated. If an `Or`-parameter exists, the rule is matched if any of the evaluation rules in the ruleset matches the event. For an `And`-parameter, all the evaluation rules must match.

The evaluation rules are simply an array of three elements in the following order:
1. The name of the parameter in the event to evaluate against. The value of that parameter will be on the _right side_ of the equation.
1. Evaluation operator to apply to the evaluation. One of the following:
    1. EQ (equals)
    1. NE (not equals)
    1. LT (less than)
    1. LE (less than or equal to)
    1. GT (greater than)
    1. GE (greater than or equal to)
    1. REGEX (evaluate against regex)
1. Value to evaluate against. This will be the value on the _left side_ of the equation.

The `transform`-object is an array of transformation rules. It allows you to make transformations to the input event's values before evaluating the rules. This is useful when your input contains, for example, an encapsulated json message. The format for the transformation rules is as follows: `<transformation>:<property-name>`, for example `json:Message` to read json from the Message-parameter. Currently the following transformations are suppported: `json`.


### Templates

The templates are written as jinja2-templates, with the exception of using `{=` and `=}` as the variable start and end strings respecively. This is to to ensure compatibility with SSMP.

All the values of the event can be found at the `data` object variable. For example, if you have an input event like this:

```json
{
    "name": "Whatever",
    "value": 13
}
```

you could create a template like this:

```
Received an event from {= data.name =} with value {= data.value =}
```

and your output would then be:
```
Received an event from Whatever with value 13
```

Remember that this data structure is dependent on the event received. The event is expected to be json, but if it is not, it will be handled as a single string input. If the input is json, you can still find a string representation of the event from the variable `datastr`. If you don't know the exact strtucture of the message, you could at first use a template that just prints out the datastr-variable:

```
{= datastr =}
```
