import pulumi
from pulumi_aws import eks
from resources import iam

config = pulumi.Config()
org = config.require("org")

"""
Get VPC resour
"""
env = pulumi.get_stack()
network = pulumi.StackReference(f"{org}/network/{env}")

vpc_config = eks.ClusterVpcConfigArgs(
        endpoint_private_access=True,
        endpoint_public_access=True,
        public_access_cidrs=["0.0.0.0/0"],
        subnet_ids=network.get_output("subnets_private"),
)

eks_cluster = eks.Cluster(
    "eks-cluster",
    version="1.27",
    role_arn=iam.eks_cluster_role.arn,
    vpc_config=vpc_config
)
