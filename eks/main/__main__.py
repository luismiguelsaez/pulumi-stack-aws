from resources import eks
from pulumi import export
from tools.kubeconfig import create_kubeconfig
from stack import aws_config, env

aws_region = aws_config.require("region")

export("eks_cluster_name", eks.eks_cluster.name)
export("eks_cluster_arn", eks.eks_cluster.arn)
export("eks_cluster_endpoint", eks.eks_cluster.endpoint)
export("eks_kubeconfig", create_kubeconfig(eks_cluster=eks.eks_cluster, region=aws_region, aws_profile=env))
export("eks_oidc_provider_arn", eks.oidc_provider.arn)
