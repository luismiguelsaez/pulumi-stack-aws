from pulumi_aws.ec2 import SecurityGroup, SecurityGroupRule
from pulumi import Config, get_stack, StackReference
from .tags import common_tags
from stack import network, eks_config

name_prefix = eks_config.require("name_prefix")

eks_cluster_node_security_group = SecurityGroup(
    f"eks-{name_prefix}-cluster-node-security-group",
    name="eks-cluster-node-security-group",
    description="Security group for EKS cluster nodes",
    vpc_id=network.get_output("vpc_id"),
    tags={
        "Name": f"eks-{name_prefix}-cluster-node-security-group",
    } | common_tags,
)
