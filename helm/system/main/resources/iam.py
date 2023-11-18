from pulumi_aws.iam import Role, Policy, RolePolicyAttachment, InstanceProfile
from pulumi import Output
import json
from stack import eks, common_tags, name_prefix
from tools.iam import create_policy_from_file, create_role_oidc, create_role_with_attached_policy
from os import path

"""
Create Karpenter IAM roles
"""
karpenter_node_role = Role(
    f"helm-{name_prefix}-karpenter-node",
    name=f"helm-{name_prefix}-karpenter-node",
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
        "Name": f"helm-{name_prefix}-karpenter-node",
    } | common_tags
)

karpenter_node_role_instance_profile = InstanceProfile(
    resource_name=f"KarpenterNodeRole-{name_prefix}",
    name=f"KarpenterNodeRole-{name_prefix}",
    role=karpenter_node_role.name,
    tags={
        "Name": f"KarpenterNodeRole-{name_prefix}",
    } | common_tags
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
    f"helm-{name_prefix}-karpenter-controller",
    name=f"helm-{name_prefix}-karpenter-controller",
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
        "Name": f"helm-{name_prefix}-karpenter-controller",
    } | common_tags
)

karpenter_role = Role(
    f"helm-{name_prefix}-karpenter-controller",
    name=f"helm-{name_prefix}-karpenter-controller",
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
        "Name": f"helm-{name_prefix}-karpenter-controller",
    } | common_tags
)

RolePolicyAttachment(
    "karpenter-policy-attachment",
    role=karpenter_role.name,
    policy_arn=karpenter_policy.arn
)

"""
Create cloud controllers roles with OIDC/WebIdentity
"""

cluster_autoscaler_role = create_role_with_attached_policy(
    f"helm-{name_prefix}-cluster-autoscaler",
    path.join(path.dirname(__file__), "policies/cluster-autoscaler.json"),
    eks.get_output("eks_oidc_provider_arn"),
    tags={
        "Name": f"helm-{name_prefix}-cluster-autoscaller-controller",
    } | common_tags
)

aws_load_balancer_controller_role = create_role_with_attached_policy(
    f"helm-{name_prefix}-aws-load-balancer-controller",
    path.join(path.dirname(__file__), "policies/aws-load-balancer-controller.json"),
    eks.get_output("eks_oidc_provider_arn"),
    tags={
        "Name": f"helm-{name_prefix}-aws-load-balancer-controller",
    } | common_tags
)

ebs_csi_driver_role = create_role_with_attached_policy(
    f"helm-{name_prefix}-ebs-csi-driver",
    path.join(path.dirname(__file__), "policies/ebs-csi-driver.json"),
    eks.get_output("eks_oidc_provider_arn"),
    tags={
        "Name": f"helm-{name_prefix}-ebs-csi-driver",
    } | common_tags
)

external_dns_role = create_role_with_attached_policy(
    f"helm-{name_prefix}-external-dns",
    path.join(path.dirname(__file__), "policies/external-dns.json"),
    eks.get_output("eks_oidc_provider_arn"),
    tags={
        "Name": f"helm-{name_prefix}-external-dns",
    } | common_tags
)

argocd_role = create_role_with_attached_policy(
    f"helm-{name_prefix}-argocd",
    path.join(path.dirname(__file__), "policies/argocd.json"),
    eks.get_output("eks_oidc_provider_arn"),
    tags={
        "Name": f"helm-{name_prefix}-argocd",
    } | common_tags
)
