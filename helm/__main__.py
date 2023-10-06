from pulumi import get_stack, export, StackReference, Config, ResourceOptions
from pulumi_kubernetes import Provider
from pulumi_kubernetes.helm.v3 import Release, RepositoryOptsArgs
from resources import iam

config = Config()
org = config.require("org")

charts = Config("charts")

"""
Get EKS resources
"""
env = get_stack()
eks = StackReference(f"{org}/eks/{env}")

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
            "defaultInstanceProfile": ""
        },
    },
    opts=ResourceOptions(provider=k8s_provider)
)
