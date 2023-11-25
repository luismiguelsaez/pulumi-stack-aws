from pulumi import StackReference, get_stack, get_project, Config
from pulumi_kubernetes import Provider

aws_config = Config("aws")
helm_config = Config("helm")
charts_config = Config("charts")
opensearch_config = Config("opensearch")
ebs_csi_driver_config = Config("ebs_csi_driver")
argocd_config = Config("argocd")
ingress_config = Config("ingress")

org = Config().require("org")
project = get_project()
env = get_stack()

name_prefix = helm_config.require("name_prefix")

common_tags = {
    "pulumi:project": project,
    "pulumi:stack": env,
}

"""
Stack references
"""
network = StackReference(f"{org}/network-{name_prefix}/{env}")
eks = StackReference(f"{org}/eks-{name_prefix}/{env}")

"""
Set Karpenter node templates discovery tags
"""
cluster_tags = {
    #f"kubernetes.io/cluster/{eks.get_output('eks_cluster_name')}": "owned",
    "aws:eks:cluster-name": f"{eks.get_output('eks_cluster_name')}",
}

discovery_tags = {
    "karpenter.sh/discovery": name_prefix,
    #"aws:eks:cluster-name": name_prefix,
}

"""
Create Kubernetes provider from EKS kubeconfig
"""
k8s_provider = Provider(
    resource_name="k8s",
    kubeconfig=eks.get_output("eks_kubeconfig"),
)
