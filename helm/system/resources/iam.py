from pulumi_aws.iam import Role, Policy, RolePolicyAttachment, InstanceProfile
from pulumi import get_stack, StackReference, Config, Output
import json

config = Config()
org = config.require("org")

"""
Get EKS resources
"""
env = get_stack()
eks = StackReference(
    name="iam-eks",
    stack_name=f"{org}/eks-main/{env}"
)

"""
Create IAM roles
"""
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

karpenter_node_role_instance_profile = InstanceProfile(
    "karpenter-node-role-instance-profile",
    name="karpenter-node-role-instance-profile",
    role=karpenter_node_role.name,
    tags={
        "Name": "karpenter-node-role-instance-profile",
        "Environment": env
    }
)

RolePolicyAttachment(
    "karpenter-node-policy-attachment-eks-worker",
    role=karpenter_node_role.name,
    policy_arn="arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy"
)

RolePolicyAttachment(
    "karpenter-node-policy-attachment-eks-cni",
    role=karpenter_node_role.name,
    policy_arn="arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy"
)

RolePolicyAttachment(
    "karpenter-node-policy-attachment-ssm",
    role=karpenter_node_role.name,
    policy_arn="arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
)

RolePolicyAttachment(
    "karpenter-node-policy-attachment-ecr",
    role=karpenter_node_role.name,
    policy_arn="arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
)

karpenter_policy = Policy(
    "karpenter-policy",
    name="karpenter-policy",
    policy=Output.json_dumps(
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "Karpenter",
                    "Effect": "Allow",
                    "Action": [
                        "ec2:CreateFleet",
                        "ec2:CreateLaunchTemplate",
                        "ec2:CreateTags",
                        "ec2:DeleteLaunchTemplate",
                        "ec2:DescribeAvailabilityZones",
                        "ec2:DescribeInstances",
                        "ec2:DescribeImages",
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
                    "Resource": ["*"]
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
                    "Effect": "Allow",
                    "Action": "iam:PassRole",
                    "Resource": karpenter_node_role.arn,
                    "Sid": "PassNodeIAMRole"
                },
                {
                    "Effect": "Allow",
                    "Action": "eks:DescribeCluster",
                    "Resource": eks.get_output("eks_cluster_arn"),
                    "Sid": "EKSClusterEndpointLookup"
                }
            ]
        }
    ),
    tags={
        "Name": "karpenter-policy",
        "Environment": env
    }
)

karpenter_role = Role(
    "karpenter-role",
    name="karpenter-role",
    assume_role_policy=Output.json_dumps(
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
    tags={
        "Name": "karpenter-role",
        "Environment": env
    }
)

RolePolicyAttachment(
    "karpenter-policy-attachment",
    role=karpenter_role.name,
    policy_arn=karpenter_policy.arn
)

cluster_autoscaler_policy = Policy(
    "cluster-autoscaler-policy",
    name="cluster-autoscaler-policy",
    policy=Output.json_dumps(
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "ClusterAutoscaler",
                    "Effect": "Allow",
                    "Action": [
                        "autoscaling:DescribeAutoScalingGroups",
                        "autoscaling:DescribeAutoScalingInstances",
                        "autoscaling:DescribeLaunchConfigurations",
                        "autoscaling:DescribeTags",
                        "ec2:DescribeInstanceTypes",
                        "ec2:DescribeLaunchTemplateVersions",
                        "autoscaling:SetDesiredCapacity",
                        "autoscaling:TerminateInstanceInAutoScalingGroup",
                        "ec2:DescribeInstanceTypes",
                        "eks:DescribeNodegroup"
                    ],
                    "Resource": "*"
                }
            ]
        }
    ),
    tags={
        "Name": "cluster-autoscaler-policy",
        "Environment": env
    }
)

cluster_autoscaler_role = Role(
    "cluster-autoscaler-role",
    name="cluster-autoscaler-role",
    assume_role_policy=Output.json_dumps(
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
    tags={
        "Name": "cluster-autoscaler-role",
        "Environment": env
    }
)

RolePolicyAttachment(
    "cluster-autoscaler-policy-attachment",
    role=cluster_autoscaler_role.name,
    policy_arn=cluster_autoscaler_policy.arn
)
