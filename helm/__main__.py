from pulumi import get_stack, export, StackReference, Config, ResourceOptions
from pulumi_kubernetes import Provider
from pulumi_kubernetes.helm.v3 import Release, RepositoryOptsArgs
from resources import iam

config = Config()
org = config.require("org")

charts = Config("charts")
aws_config = Config("aws")

"""
Get EKS resources
"""
env = get_stack()
eks = StackReference(f"{org}/eks-main/{env}")

"""
Create Kubernetes provider from EKS kubeconfig
"""
k8s_provider = Provider(
    resource_name="k8s",
    kubeconfig=eks.get_output("eks_kubeconfig"),
)

karpenter_helm_release = Release(
    "karpenter-helm-release",
    repository_opts=RepositoryOptsArgs(
        repo="https://charts.karpenter.sh"
    ),
    version=charts.require("karpenter_version"),
    chart="karpenter",
    namespace="kube-system",
    name="karpenter",
    values={
        "controller": {
            "logLevel": "info",
        },
        "serviceAccount": {
            "create": True,
            "anntations": {
                "eks.amazonaws.com/role-arn": iam.karpenter_role.arn,
            }
        },
        "clusterName": eks.get_output("eks_cluster_name"),
        "clusterEndpoint": eks.get_output("eks_cluster_endpoint"),
        "aws": {
            "defaultInstanceProfile": iam.karpenter_node_role_instance_profile.name,
        },
    },
    opts=ResourceOptions(provider=k8s_provider)
)

cluster_autoscaler_helm_release = Release(
    "cluster-autoscaler-helm-release",
    repository_opts=RepositoryOptsArgs(
        repo="https://kubernetes.github.io/autoscaler"
    ),
    version=charts.require("cluster_autoscaler_version"),
    chart="cluster-autoscaler",
    namespace="kube-system",
    name="cluster-autoscaler",
    values={
        "autoDiscovery": {
            "clusterName": eks.get_output("eks_cluster_name"),
        },
        "awsRegion": aws_config.require("region"),
        "rbac": {
            "create": True,
            "serviceAccount": {
                "create": True,
                "annotations": {
                    "eks.amazonaws.com/role-arn": iam.cluster_autoscaler_role.arn,
                }
            },
        },
        "extraArgs": {
            "balance-similar-node-groups": True,
            "skip-nodes-with-system-pods": False,
        },
    },
    opts=ResourceOptions(provider=k8s_provider)
)
