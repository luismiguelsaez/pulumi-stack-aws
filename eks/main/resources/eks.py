from pulumi import ResourceOptions, InvokeOptions
from pulumi_aws import eks
from pulumi_aws.iam import OpenIdConnectProvider
import json
from . import iam, ec2
from tools import http
from stack import network, aws_config, common_tags, discovery_tags, name_prefix, eks_version, eks_config

"""
Create EKS cluster
"""
eks_cluster = eks.Cluster(
    name=f"{name_prefix}",
    resource_name=f"{name_prefix}",
    version=eks_version,
    role_arn=iam.eks_cluster_role.arn,
    vpc_config=eks.ClusterVpcConfigArgs(
        endpoint_private_access=True,
        endpoint_public_access=True,
        public_access_cidrs=["0.0.0.0/0"],
        subnet_ids=network.get_output("subnets_private"),
        #cluster_security_group_id=ec2.eks_cluster_security_group.id,
        security_group_ids=[ec2.eks_cluster_node_security_group.id]
    ),
    tags={
        "Name": f"{name_prefix}",
    } | common_tags | discovery_tags,
)

"""
Create EKS OIDC provider
"""
oidc_fingerprint = http.get_ssl_cert_fingerprint(host=f"oidc.eks.{aws_config.require('region')}.amazonaws.com")
oidc_provider = OpenIdConnectProvider(
    f"eks-{name_prefix}",
    client_id_lists=["sts.amazonaws.com"],
    thumbprint_lists=[oidc_fingerprint],
    url=eks_cluster.identities[0].oidcs[0].issuer,
    tags={
        "Name": f"eks-{name_prefix}",
    } | common_tags,
    opts=ResourceOptions(depends_on=[eks_cluster]),
)

"""
Create EKS node group
"""
eks_nodegroup_system = eks.NodeGroup(
    resource_name=f"{name_prefix}-system",
    cluster_name=eks_cluster.name,
    node_group_name=f"{name_prefix}-system",
    node_role_arn=iam.eks_node_role.arn,
    subnet_ids=network.get_output("subnets_private"),
    scaling_config=eks.NodeGroupScalingConfigArgs(
        max_size=eks_config.require("node_group_size_max"),
        desired_size=eks_config.require("node_group_size_desired"),
        min_size=eks_config.require("node_group_size_min"),
    ),
    instance_types=["t4g.medium", "t4g.large"],
    capacity_type="ON_DEMAND",
    ami_type="BOTTLEROCKET_ARM_64",
    disk_size=20,
    update_config=eks.NodeGroupUpdateConfigArgs(
        max_unavailable=1,
    ),
    tags={
        "Name": f"{name_prefix}-system",
    } | common_tags,
)

"""
Addons setup
"""
eks_addon_coredns = eks.Addon(
    resource_name=f"{name_prefix}-coredns",
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
        "Name": f"{name_prefix}-coredns",
    } | common_tags,
    opts=ResourceOptions(depends_on=[eks_nodegroup_system])
)
