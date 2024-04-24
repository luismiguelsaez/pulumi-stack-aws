from pulumi import Output
from os import path
import json
from pulumi_aws.iam import Role, Policy, RolePolicyAttachment

def create_policy_from_file(name: str, policy_file: str, tags: dict = {})->Policy:

    with open(path.join(path.dirname(__file__), policy_file)) as f:
        policy_json = json.loads(f.read())

    policy = Policy(
        name,
        name=name,
        policy=Output.json_dumps(policy_json),
        tags=tags
    )
    
    return policy

def create_role_oidc(name, oidc_provider_arn: Output, tags: dict = {})->Role:

    role = Role(
        name,
        name=name,
        assume_role_policy=Output.json_dumps(
            {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Action": "sts:AssumeRoleWithWebIdentity",
                        "Principal": {
                            "Federated": oidc_provider_arn.apply(lambda arn: arn)
                        },
                        "Effect": "Allow",
                        "Sid": "",
                    },
                ],
            }
        ),
        tags=tags
    )

    return role

def create_role_with_attached_policy(name: str, policy_file: str, oidc_provider_arn: Output, tags: dict = {})->Role:

    policy = create_policy_from_file(name, policy_file, tags)
    role = create_role_oidc(name, oidc_provider_arn, tags)
    role_policy_attachment = RolePolicyAttachment(
        f"{name}-main",
        role=role.name,
        policy_arn=policy.arn
    )
    
    return role
