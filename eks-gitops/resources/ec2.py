from pulumi_aws.ec2 import SecurityGroup, SecurityGroupEgressArgs, SecurityGroupIngressArgs
from . import vpc
from common import stack_config, common_tags, discovery_tags

eks_cluster_node_security_group = SecurityGroup(
    f"eks-{stack_config.require('name')}-cluster-node-security-group",
    name="eks-cluster-node-security-group",
    description="Security group for EKS cluster nodes",
    vpc_id=vpc.vpc.id,
    egress=[
        SecurityGroupEgressArgs(
            description="Allow all outbound traffic by default",
            protocol="-1",
            from_port=0,
            to_port=0,
            cidr_blocks=["0.0.0.0/0"],
        )
    ],
    ingress=[
        SecurityGroupIngressArgs(
            description="Allow SSH connections from anywhere",
            protocol="tcp",
            from_port=22,
            to_port=22,
            cidr_blocks=["0.0.0.0/0"],
        )
    ],
    tags={
        "Name": f"eks-{stack_config.require('name')}-cluster-node-security-group",
    } | common_tags | discovery_tags,
)

#eks_cluster_security_group = SecurityGroup(
#    f"eks-{stack_config.require('name')}-cluster-security-group",
#    name="eks-cluster-security-group",
#    description="Security group for EKS cluster",
#    vpc_id=network.get_output("vpc_id"),
#    egress=[
#        SecurityGroupEgressArgs(
#            description="Allow all outbound traffic by default",
#            protocol="-1",
#            from_port=0,
#            to_port=0,
#            cidr_blocks=["0.0.0.0/0"],
#        )
#    ],
#    ingress=[
#        SecurityGroupIngressArgs(
#            description="Allow all inbound traffic from self",
#            protocol="-1",
#            from_port=0,
#            to_port=0,
#            self=True,
#        ),
#        SecurityGroupIngressArgs(
#            description="Allow all inbound traffic from nodes",
#            protocol="-1",
#            from_port=0,
#            to_port=0,
#            security_groups=[eks_cluster_node_security_group.id],
#        )
#    ],
#    tags={
#        "Name": f"eks-{stack_config.require('name')}-cluster-security-group"
#    } | cluster_tags | common_tags | discovery_tags,
#)
