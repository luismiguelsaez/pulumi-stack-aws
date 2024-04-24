from pulumi_aws.iam import Role, RolePolicyAttachment, InstanceProfile
import json
from common import stack_config, common_tags

### EKS ###

eks_cluster_role = Role(
    f"eks-{stack_config.require('name')}-cluster",
    assume_role_policy=json.dumps(
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "sts:AssumeRole",
                    "Principal": {
                        "Service": "eks.amazonaws.com"
                    },
                    "Effect": "Allow",
                    "Sid": ""
                }
            ]
        }
    ),
    tags={
        "Name": f"eks-{stack_config.require('name')}-cluster",
    } | common_tags,
)

RolePolicyAttachment(
    f"eks-{stack_config.require('name')}-AmazonEKSClusterPolicy",
    policy_arn="arn:aws:iam::aws:policy/AmazonEKSClusterPolicy",
    role=eks_cluster_role.name,
)

RolePolicyAttachment(
    f"eks-{stack_config.require('name')}-AmazonEKSServicePolicy",
    policy_arn="arn:aws:iam::aws:policy/AmazonEKSServicePolicy",
    role=eks_cluster_role.name,
)

"""
Node IAM role
"""
eks_node_role = Role(
    f"eks-{stack_config.require('name')}-node",
    assume_role_policy=json.dumps(
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "sts:AssumeRole",
                    "Principal": {
                        "Service": "ec2.amazonaws.com"
                    },
                    "Effect": "Allow",
                    "Sid": ""
                }
            ]
        }
    ),
    tags={
        "Name": f"eks-{stack_config.require('name')}-node",
    } | common_tags,
)

eks_node_role_instance_profile = InstanceProfile(
    f"eks-{stack_config.require('name')}-node",
    role=eks_node_role.name,
    tags={
        "Name": f"eks-{stack_config.require('name')}-node",
    } | common_tags,
)

RolePolicyAttachment(
    f"eks-{stack_config.require('name')}-node-AmazonEKSWorkerNodePolicy",
    policy_arn="arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy",
    role=eks_node_role.name,
)

RolePolicyAttachment(
    f"eks-{stack_config.require('name')}-node-AmazonEKS_CNI_Policy",
    policy_arn="arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy",
    role=eks_node_role.name,
)

RolePolicyAttachment(
    f"eks-{stack_config.require('name')}-node-AmazonSSMManagedInstanceCore",
    policy_arn="arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly",
    role=eks_node_role.name,
)
