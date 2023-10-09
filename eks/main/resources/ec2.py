from pulumi_aws.ec2 import SecurityGroup, SecurityGroupEgressArgs, SecurityGroupIngressArgs
from stack import network, eks_config, common_tags, discovery_tags

name_prefix = eks_config.require("name_prefix")

eks_cluster_node_security_group = SecurityGroup(
    f"eks-{name_prefix}-cluster-node-security-group",
    name="eks-cluster-node-security-group",
    description="Security group for EKS cluster nodes",
    vpc_id=network.get_output("vpc_id"),
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
        "Name": f"eks-{name_prefix}-cluster-node-security-group",
    } | common_tags | discovery_tags,
)
