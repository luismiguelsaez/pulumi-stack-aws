from resources import eks
from pulumi import export

export("eks_cluster_name", eks.eks_cluster.name)
export("eks_cluster_endpoint", eks.eks_cluster.endpoint)
