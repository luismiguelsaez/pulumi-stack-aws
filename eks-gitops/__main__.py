"""An AWS Python Pulumi program"""

from pulumi import export
from resources import vpc, eks, iam
from common import aws_config, env
from tools.kubeconfig import create_kubeconfig


aws_region = aws_config.require("region")

export("vpc_id", vpc.vpc.id)
export("subnets_public", [ subnet.id for subnet in vpc.subnets_public ])
export("subnets_private", [ subnet.id for subnet in vpc.subnets_private ])
export("availability_zones", vpc.azs.names)

export("eks_cluster_name", eks.eks_cluster.name)
export("eks_cluster_arn", eks.eks_cluster.arn)
export("eks_cluster_endpoint", eks.eks_cluster.endpoint)
export("eks_cluster_ca_data", eks.eks_cluster.certificate_authority.data)
export("eks_kubeconfig", create_kubeconfig(eks_cluster=eks.eks_cluster, region=aws_region, aws_profile=env))
export("eks_oidc_provider_arn", eks.oidc_provider.arn)
export("eks_nodegroup_system_role_arn", iam.eks_node_role.arn)
