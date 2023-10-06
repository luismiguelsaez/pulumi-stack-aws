from pulumi import get_stack, StackReference, Config
from pulumi_aws import eks
from . import iam

config = Config()
org = config.require("org")

"""
Get VPC resources
"""
env = get_stack()
network = StackReference(f"{org}/network/{env}")

"""
Get EKS config
"""
eks_config = Config("eks")
eks_name_prefix = eks_config.require("name_prefix")
eks_version = eks_config.require("version")

"""
Create EKS cluster
"""
eks_cluster = eks.Cluster(
    resource_name=f"{eks_name_prefix}",
    version=eks_version,
    role_arn=iam.eks_cluster_role.arn,
    vpc_config=eks.ClusterVpcConfigArgs(
        endpoint_private_access=True,
        endpoint_public_access=True,
        public_access_cidrs=["0.0.0.0/0"],
        subnet_ids=network.get_output("subnets_private"),
        security_group_ids=[]
    ),
    tags={
        "Name": f"{eks_name_prefix}",
        "Environment": env
    }
)
