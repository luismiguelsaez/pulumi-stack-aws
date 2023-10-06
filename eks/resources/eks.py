from pulumi import get_stack, StackReference, Config, ResourceOptions
from pulumi_aws import eks
import json
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

"""
Create EKS node group
"""
eks_nodegroup_system = eks.NodeGroup(
    resource_name=f"{eks_name_prefix}-system",
    cluster_name=eks_cluster.name,
    node_group_name=f"{eks_name_prefix}-system",
    node_role_arn=iam.eks_node_role.arn,
    subnet_ids=network.get_output("subnets_private"),
    scaling_config=eks.NodeGroupScalingConfigArgs(
        desired_size=3,
        max_size=10,
        min_size=3
    ),
    instance_types=["t4g.medium", "t4g.large"],
    capacity_type="ON_DEMAND",
    ami_type="BOTTLEROCKET_ARM_64",
    disk_size=20,
)

"""
Addons setup
"""
eks_addon_coredns = eks.Addon(
    resource_name=f"{eks_name_prefix}-coredns",
    cluster_name=eks_cluster.name,
    addon_name="coredns",
    resolve_conflicts_on_create="OVERWRITE",
    resolve_conflicts_on_update="OVERWRITE",
    configuration_values=json.dumps(
        {
            "replicaCount": 4,
            "resources": {
                "limits": {
                    "cpu": "100m",
                    "memory": "200Mi"
                },
                "requests": {
                    "cpu": "100m",
                    "memory": "200Mi"
                }
            }
        }
    ),
    opts=ResourceOptions(depends_on=[eks_nodegroup_system])
)
