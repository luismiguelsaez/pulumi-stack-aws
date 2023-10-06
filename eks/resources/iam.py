from pulumi_aws.iam import Role, RolePolicyAttachment, InstanceProfile
import json

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
    },
)

RolePolicyAttachment(
    "AmazonEKSClusterPolicy",
    policy_arn="arn:aws:iam::aws:policy/AmazonEKSClusterPolicy",
    role=eks_cluster_role.name,
)

RolePolicyAttachment(
    "AmazonEKSServicePolicy",
    policy_arn="arn:aws:iam::aws:policy/AmazonEKSServicePolicy",
    role=eks_cluster_role.name,
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
    },
)

eks_node_role_instance_profile = InstanceProfile(
    "eks-node-role",
    role=eks_node_role.name,
)

RolePolicyAttachment(
    "eks-nodegroup-AmazonEKSWorkerNodePolicy",
    policy_arn="arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy",
    role=eks_node_role.name,
)

RolePolicyAttachment(
    "eks-nodegroup-AmazonEKS_CNI_Policy",
    policy_arn="arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy",
    role=eks_node_role.name,
)

RolePolicyAttachment(
    "eks-nodegroup-AmazonEC2ContainerRegistryReadOnly",
    policy_arn="arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly",
    role=eks_node_role.name,
)
