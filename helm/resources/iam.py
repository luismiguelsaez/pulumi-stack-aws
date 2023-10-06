from pulumi_aws.iam import Role, Policy, RolePolicyAttachment
from pulumi import get_stack, StackReference, Config
import json

config = Config()
org = config.require("org")

"""
Get EKS resources
"""
env = get_stack()
eks = StackReference(f"{org}/eks/{env}")

"""
Create IAM roles
"""
karpenter_role = Role(
    "karpenter-role",
    name="karpenter-role",
    assume_role_policy=json.dumps(
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "",
                    "Effect": "Allow",
                    "Principal": {
                        "Federated": eks.get_output("eks_oidc_provider_arn")
                    },
                    "Action": "sts:AssumeRoleWithWebIdentity"
                }
            ]
        }
    ),
    policy=json.dumps(
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": [
                        "ec2:CreateFleet",
                        "ec2:CreateLaunchTemplate",
                        "ec2:CreateTags",
                        "ec2:DeleteLaunchTemplate",
                        "ec2:DescribeAvailabilityZones",
                        "ec2:DescribeInstances",
                        "ec2:DescribeInstanceTypeOfferings",
                        "ec2:DescribeInstanceTypes",
                        "ec2:DescribeLaunchTemplates",
                        "ec2:DescribeSecurityGroups",
                        "ec2:DescribeSpotPriceHistory",
                        "ec2:DescribeSubnets",
                        "ec2:RunInstances",
                        "iam:PassRole",
                        "pricing:GetProducts",
                        "ssm:GetParameter"
                    ],
                    "Effect": "Allow",
                    "Resource": [
                        "*"
                    ],
                    "Sid": "Karpenter"
                },
                {
                    "Action": "ec2:TerminateInstances",
                    "Condition": {
                        "StringLike": {
                            "ec2:ResourceTag/karpenter.sh/provisioner-name": "*"
                        }
                    },
                    "Effect": "Allow",
                    "Resource": "*",
                    "Sid": "ConditionalEC2Termination"
                },
                {
                    "Action": "iam:PassRole",
                    "Effect": "Allow",
                    "Resource": "arn:aws:iam::632374391739:role/lok-k8s-main-KarpenterNode",
                    "Sid": "PassNodeIAMRole"
                },
                {
                    "Action": "eks:DescribeCluster",
                    "Effect": "Allow",
                    "Resource": "arn:aws:eks:aws:632374391739:cluster/lok-k8s-main",
                    "Sid": "EKSClusterEndpointLookup"
                }
            ],
        }
    ),
    tags={
        "Name": "karpenter-role",
        "Environment": env
    }
)

karpenter_node_role = Role(
    "karpenter-node-role",
    name="karpenter-node-role",
    assume_role_policy=json.dumps(
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "",
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "ec2.amazonaws.com"
                    },
                    "Action": "sts:AssumeRole"
                }
            ]
        }
    ),
    tags={
        "Name": "karpenter-node-role",
        "Environment": env
    }
)
