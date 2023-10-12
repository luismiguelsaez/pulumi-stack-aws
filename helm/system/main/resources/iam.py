from pulumi_aws.iam import Role, Policy, RolePolicyAttachment, InstanceProfile
from pulumi import Output
import json
from stack import eks, common_tags, name_prefix


"""
Create IAM roles
"""
karpenter_node_role = Role(
    f"helm-{name_prefix}-karpenter-node",
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
        "Name": f"helm-{name_prefix}-karpenter-node",
    } | common_tags
)

karpenter_node_role_instance_profile = InstanceProfile(
    f"helm-{name_prefix}-karpenter-node",
    name="karpenter-node-role-instance-profile",
    role=karpenter_node_role.name,
    tags={
        "Name": "karpenter-node-role-instance-profile",
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
        "Name": f"helm-{name_prefix}-karpenter-controller",
    } | common_tags
)

karpenter_role = Role(
    f"helm-{name_prefix}-karpenter-controller",
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
        "Name": f"helm-{name_prefix}-karpenter-controller",
    } | common_tags
)

RolePolicyAttachment(
    "karpenter-policy-attachment",
    role=karpenter_role.name,
    policy_arn=karpenter_policy.arn
)

cluster_autoscaler_policy = Policy(
    f"helm-{name_prefix}-cluster-autoscaller-controller",
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
        "Name": f"helm-{name_prefix}-cluster-autoscaller-controller",
    } | common_tags
)

cluster_autoscaler_role = Role(
    f"helm-{name_prefix}-cluster-autoscaller-controller",
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
        "Name": f"helm-{name_prefix}-cluster-autoscaller-controller",
    } | common_tags
)

RolePolicyAttachment(
    "cluster-autoscaler-policy-attachment",
    role=cluster_autoscaler_role.name,
    policy_arn=cluster_autoscaler_policy.arn
)
