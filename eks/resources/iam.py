from pulumi_aws.iam import Role, RolePolicyAttachment

eks_cluster_role = Role(
    "eks-cluster-role",
    assume_role_policy="""{
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
    }""",
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
