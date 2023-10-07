from resources import eks
from pulumi import Config, export, get_stack
from tools.kubeconfig import create_kubeconfig

aws_config = Config("aws")
aws_region = aws_config.require("region")

env = get_stack()

export("eks_cluster_name", eks.eks_cluster.name)
export("eks_cluster_arn", eks.eks_cluster.arn)
export("eks_cluster_endpoint", eks.eks_cluster.endpoint)
export("eks_kubeconfig", create_kubeconfig(eks_cluster=eks.eks_cluster, region=aws_region, aws_profile=env))
export("eks_oidc_provider_arn", eks.oidc_provider.arn)
