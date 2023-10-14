from pulumi import ResourceOptions, export, Output
from pulumi_kubernetes.core.v1 import ConfigMap, ConfigMapPatch
from pulumi_kubernetes.meta.v1 import ObjectMetaPatchArgs
from pulumi_kubernetes.helm.v3 import Release, RepositoryOptsArgs
from resources import iam
from stack import aws_config, charts_config, eks, cluster_tags, discovery_tags, k8s_provider
from tools import karpenter
from requests import get

"""
Setup aws-auth ConfigMap for Karpenter
"""
aws_auth_cm = ConfigMap.get(
    "aws-auth",
    id="kube-system/aws-auth",
    opts=ResourceOptions(provider=k8s_provider)
)

if not aws_auth_cm.metadata.annotations["karpenter.sh/config"]:

    karpenter_role_mapping = iam.karpenter_node_role.arn.apply(lambda arn: f"""
- rolearn: {arn}
  username: system:node:{{{{EC2PrivateDNSName}}}}
  groups:
  - system:bootstrappers
  - system:nodes
""")

else:

    karpenter_role_mapping = ""

existing_map_roles = aws_auth_cm.data['mapRoles']

new_map_roles = Output.concat(
    existing_map_roles,
    karpenter_role_mapping
)

ConfigMapPatch(
    "karpenter-aws-auth-cm-patch",
    api_version=aws_auth_cm.api_version,
    kind=aws_auth_cm.kind,
    metadata=ObjectMetaPatchArgs(
        name="aws-auth",
        namespace="kube-system",
        annotations={
            "pulumi.com/patchForce": "true",
            "karpenter.sh/config": "true"
        }
    ),
    data={
        "mapRoles": new_map_roles
    },
    opts=ResourceOptions(provider=k8s_provider)
)

"""
Deploy Karpenter Helm chart
"""
karpenter_helm_release = Release(
    "karpenter-helm-release",
    repository_opts=RepositoryOptsArgs(
        repo="https://charts.karpenter.sh",
    ),
    version=charts_config.require("karpenter_version"),
    chart="karpenter",
    namespace="kube-system",
    name="karpenter",
    values={
        "controller": {
            "logLevel": "info",
        },
        "serviceAccount": {
            "create": True,
            "annotations": {
                "eks.amazonaws.com/role-arn": iam.karpenter_role.arn,
            }
        },
        "clusterName": eks.get_output("eks_cluster_name"),
        "clusterEndpoint": eks.get_output("eks_cluster_endpoint"),
        "aws": {
            "defaultInstanceProfile": iam.karpenter_node_role_instance_profile.name,
            "vmMemoryOverheadPercent": 0.075
        },
    },
    opts=ResourceOptions(provider=k8s_provider)
)

"""
Deploy Cluster Autoscaler Helm chart
"""
cluster_autoscaler_helm_release = Release(
    "cluster-autoscaler-helm-release",
    repository_opts=RepositoryOptsArgs(
        repo="https://kubernetes.github.io/autoscaler"
    ),
    version=charts_config.require("cluster_autoscaler_version"),
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

"""
Provision Karpenter AWSNodetemplates
"""
public_ssh_key = get("https://github.com/luismiguelsaez.keys").text.strip()

karpenter.karpenter_templates(
    name="karpenter-aws-node-templates",
    provider=k8s_provider,
    manifests_path="resources/nodetemplates",
    eks_cluster_name=eks.get_output("eks_cluster_name"),
    ssh_public_key=public_ssh_key,
    sg_selector_tags=cluster_tags,
    subnet_selector_tags=discovery_tags,
    depends_on=[karpenter_helm_release]
)
