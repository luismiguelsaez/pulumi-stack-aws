from pulumi import Output
from pulumi_aws import iam, get_caller_identity
from stack import name_prefix, aws_config

current = get_caller_identity()

iam_policy_secrets_manager = iam.Policy(
    resource_name=f'ecs-cluster-{name_prefix}-secrets-manager',
    name="secrets-manager",
    policy=Output.json_dumps(
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "secretsmanager:GetResourcePolicy",
                        "secretsmanager:GetSecretValue",
                        "secretsmanager:DescribeSecret",
                        "secretsmanager:ListSecretVersionIds"
                    ],
                    "Resource": [
                        f"arn:aws:secretsmanager:{aws_config.get('region')}:{current.account_id}:secret:/ecs/cluster/*",
                    ]
                },
                {
                    "Effect": "Allow",
                    "Action": "secretsmanager:ListSecrets",
                    "Resource": "*"
                }
            ]
        }
    )
)

iam_role_task_execution = iam.Role(
    resource_name=f'ecs-cluster-{name_prefix}-task-execution',
    name="task-execution",
    assume_role_policy=Output.json_dumps(
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "ecs-tasks.amazonaws.com"
                    },
                    "Action": "sts:AssumeRole"
                }
            ]
        }
    )
)

iam_role_policy_attachment_secrets_manager = iam.RolePolicyAttachment(
    resource_name=f'ecs-cluster-{name_prefix}-task-execution-secrets-manager',
    role=iam_role_task_execution.name,
    policy_arn=iam_policy_secrets_manager.arn,
)
