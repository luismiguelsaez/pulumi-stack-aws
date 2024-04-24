from pulumi_aws.iam import Policy, Role, RolePolicyAttachment, InstanceProfile
from pulumi_aws import get_caller_identity
from pulumi import Output
from . import eks
import json
from common import aws_config, stack_config, common_tags
from tools.iam import create_role_with_attached_policy
from os import path

### HELM ###

"""
Create Karpenter IAM roles
"""
karpenter_node_role = Role(
    f"helm-{stack_config.require('name')}-karpenter-node",
    name=f"helm-{stack_config.require('name')}-karpenter-node",
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
        "Name": f"helm-{stack_config.require('name')}-karpenter-node",
    } | common_tags
)

karpenter_node_role_instance_profile = InstanceProfile(
    resource_name=f"KarpenterNodeRole-{stack_config.require('name')}",
    name=f"KarpenterNodeRole-{stack_config.require('name')}",
    role=karpenter_node_role.name,
    tags={
        "Name": f"KarpenterNodeRole-{stack_config.require('name')}",
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
    f"helm-{stack_config.require('name')}-karpenter-controller",
    name=f"helm-{stack_config.require('name')}-karpenter-controller",
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
                        "ec2:TerminateInstances",
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
                    "Resource": eks.eks_cluster.arn,
                    "Sid": "EKSClusterEndpointLookup"
                }
            ]
        }
    ),
    tags={
        "Name": f"helm-{stack_config.require('name')}-karpenter-controller",
    } | common_tags
)

karpenter_role = Role(
    f"helm-{stack_config.require('name')}-karpenter-controller",
    name=f"helm-{stack_config.require('name')}-karpenter-controller",
    assume_role_policy=Output.json_dumps(
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "",
                    "Effect": "Allow",
                    "Principal": {
                        "Federated": eks.oidc_provider.arn
                    },
                    "Action": "sts:AssumeRoleWithWebIdentity"
                }
            ]
        }
    ),
    tags={
        "Name": f"helm-{stack_config.require('name')}-karpenter-controller",
    } | common_tags
)

RolePolicyAttachment(
    "karpenter-policy-attachment",
    role=karpenter_role.name,
    policy_arn=karpenter_policy.arn
)

current = get_caller_identity()

argocd_policy = Policy(
    f"helm-{stack_config.require('name')}-argocd",
    name=f"helm-{stack_config.require('name')}-argocd",
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
                        f"arn:aws:secretsmanager:{aws_config.get('region')}:{current.account_id}:secret:/eks/cluster/*",
                    ]
                },
                {
                    "Effect": "Allow",
                    "Action": "secretsmanager:ListSecrets",
                    "Resource": "*"
                }
            ]
        }
    ),
)

argocd_role = Role(
    f"helm-{stack_config.require('name')}-argocd",
    name=f"helm-{stack_config.require('name')}-argocd",
    assume_role_policy=Output.json_dumps(
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "",
                    "Effect": "Allow",
                    "Principal": {
                        "Federated": eks.oidc_provider.arn
                    },
                    "Action": "sts:AssumeRoleWithWebIdentity"
                }
            ]
        }
    ),
    tags={
        "Name": f"helm-{stack_config.require('name')}-argocd",
    } | common_tags
)

RolePolicyAttachment(
    f"helm-{stack_config.require('name')}-argocd-main",
    role=argocd_role.name,
    policy_arn=argocd_policy.arn
)

"""
Create cloud controllers roles with OIDC/WebIdentity
"""

cluster_autoscaler_role = create_role_with_attached_policy(
    f"helm-{stack_config.require('name')}-cluster-autoscaler",
    path.join(path.dirname(__file__), "policies/cluster-autoscaler.json"),
    eks.oidc_provider.arn,
    tags={
        "Name": f"helm-{stack_config.require('name')}-cluster-autoscaller-controller",
    } | common_tags
)

aws_load_balancer_controller_role = create_role_with_attached_policy(
    f"helm-{stack_config.require('name')}-aws-load-balancer-controller",
    path.join(path.dirname(__file__), "policies/aws-load-balancer-controller.json"),
    eks.oidc_provider.arn,
    tags={
        "Name": f"helm-{stack_config.require('name')}-aws-load-balancer-controller",
    } | common_tags
)

ebs_csi_driver_role = create_role_with_attached_policy(
    f"helm-{stack_config.require('name')}-ebs-csi-driver",
    path.join(path.dirname(__file__), "policies/ebs-csi-driver.json"),
    eks.oidc_provider.arn,
    tags={
        "Name": f"helm-{stack_config.require('name')}-ebs-csi-driver",
    } | common_tags
)

external_dns_role = create_role_with_attached_policy(
    f"helm-{stack_config.require('name')}-external-dns",
    path.join(path.dirname(__file__), "policies/external-dns.json"),
    eks.oidc_provider.arn,
    tags={
        "Name": f"helm-{stack_config.require('name')}-external-dns",
    } | common_tags
)

#argocd_role = create_role_with_attached_policy(
#    f"helm-{stack_config.require('name')}-argocd",
#    path.join(path.dirname(__file__), "policies/argocd.json"),
#    eks.oidc_provider.arn,
#    tags={
#        "Name": f"helm-{stack_config.require('name')}-argocd",
#    } | common_tags
#)
