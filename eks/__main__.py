from resources import eks
from pulumi import Config, export
from tools.kubeconfig import create_kubeconfig

aws_config = Config("aws")
aws_region = aws_config.require("region")

export("eks_cluster_name", eks.eks_cluster.name)
export("eks_cluster_endpoint", eks.eks_cluster.endpoint)
export("eks_kubeconfig", create_kubeconfig(eks_cluster=eks.eks_cluster, region=aws_region))
