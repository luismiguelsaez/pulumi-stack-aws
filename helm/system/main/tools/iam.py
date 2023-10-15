from pulumi import Output
from os import path
import json
from pulumi_aws.iam import Role, Policy

def create_policy_from_file(name: str, policy_file: str)->Policy:

    with open(path.join(path.dirname(__file__), policy_file)) as f:
        policy_json = json.loads(f.read())

    policy = Policy(
        name,
        policy=Output.json_dumps(policy_json)
    )
    
    return policy

def create_role_oidc(name, oidc_provider_arn: str)->Role:

    role = Role(
        name,
        assume_role_policy=Output.json_dumps(
            {
            "Version": "2012-10-17",
            "Statement": [
                {
                "Action": "sts:AssumeRoleWithWebIdentity",
                "Principal": {
                    "Federated": oidc_provider_arn
                },
                "Effect": "Allow",
                "Sid": "",
                },
            ],
            }
        )
    )

    return role
