from pulumi import StackReference, get_stack, get_project, Config
from pulumi_kubernetes import Provider

aws_config = Config("aws")
helm_config = Config("helm")
charts_config = Config("charts")
opensearch_config = Config("opensearch")
argocd_config = Config("argocd")

org = Config().require("org")
project = get_project()
env = get_stack()

name_prefix = helm_config.require("name_prefix")

common_tags = {
    "pulumi:project": project,
    "pulumi:stack": env,
}

cluster_tags = {
    f"kubernetes.io/cluster/{name_prefix}": "owned",
}

discovery_tags = {
    "karpenter.sh/discovery": name_prefix,
}

"""
Stack references
"""
network = StackReference(f"{org}/network-{name_prefix}/{env}")
eks = StackReference(f"{org}/eks-{name_prefix}/{env}")

"""
Create Kubernetes provider from EKS kubeconfig
"""
k8s_provider = Provider(
    resource_name="k8s",
    kubeconfig=eks.get_output("eks_kubeconfig"),
)
