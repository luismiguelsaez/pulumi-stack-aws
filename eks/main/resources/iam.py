from pulumi_aws.iam import Role, RolePolicyAttachment, InstanceProfile
from pulumi import get_project, get_stack
import json
from .tags import common_tags

eks_cluster_role = Role(
    "eks-cluster-role",
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
        "Name": "eks-cluster-role",
    } | common_tags,
)

RolePolicyAttachment(
    "AmazonEKSClusterPolicy",
    policy_arn="arn:aws:iam::aws:policy/AmazonEKSClusterPolicy",
    role=eks_cluster_role.name,
    tags={
        "Name": "AmazonEKSClusterPolicy",
    } | common_tags,
)

RolePolicyAttachment(
    "AmazonEKSServicePolicy",
    policy_arn="arn:aws:iam::aws:policy/AmazonEKSServicePolicy",
    role=eks_cluster_role.name,
    tags={
        "Name": "AmazonEKSServicePolicy",
    } | common_tags,
)

"""
Node IAM role
"""
eks_node_role = Role(
    "eks-node-role",
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
        "Name": "eks-node-role",
    } | common_tags,
)

eks_node_role_instance_profile = InstanceProfile(
    "eks-node-role",
    role=eks_node_role.name,
    tags={
        "Name": "eks-node-role",
    } | common_tags,
)

RolePolicyAttachment(
    "eks-nodegroup-AmazonEKSWorkerNodePolicy",
    policy_arn="arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy",
    role=eks_node_role.name,
    tags={
        "Name": "AmazonEKSWorkerNodePolicy",
    } | common_tags,
)

RolePolicyAttachment(
    "eks-nodegroup-AmazonEKS_CNI_Policy",
    policy_arn="arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy",
    role=eks_node_role.name,
    tags={
        "Name": "AmazonEKS_CNI_Policy",
    } | common_tags,
)

RolePolicyAttachment(
    "eks-nodegroup-AmazonEC2ContainerRegistryReadOnly",
    policy_arn="arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly",
    role=eks_node_role.name,
    tags={
        "Name": "AmazonEC2ContainerRegistryReadOnly",
    } | common_tags,
)
