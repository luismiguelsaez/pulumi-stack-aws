from pulumi import get_stack, get_project, StackReference, Config, ResourceOptions
from pulumi_aws import eks
from pulumi_aws.iam import OpenIdConnectProvider
import json
from . import iam
from tools import http
from .tags import common_tags

config = Config()
org = config.require("org")

aws_config = Config("aws")

"""
Get VPC resources
"""
env = get_stack()
network = StackReference(f"{org}/network-main/{env}")

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
    } | common_tags,
)

"""
Create EKS OIDC provider
"""
oidc_fingerprint = http.get_ssl_cert_fingerprint(host=f"oidc.eks.{aws_config.require('region')}.amazonaws.com")
oidc_provider = OpenIdConnectProvider(
    f"{eks_name_prefix}-oidc-provider",
    client_id_lists=["sts.amazonaws.com"],
    thumbprint_lists=[oidc_fingerprint],
    url=eks_cluster.identities[0].oidcs[0].issuer,
    tags={
        "Name": f"{eks_name_prefix}-oidc-provider",
    } | common_tags,
    opts=ResourceOptions(depends_on=[eks_cluster]),
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
    tags={
        "Name": f"{eks_name_prefix}-system",
    } | common_tags,
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
    tags={
        "Name": f"{eks_name_prefix}-coredns",
    } | common_tags,
    opts=ResourceOptions(depends_on=[eks_nodegroup_system])
)
