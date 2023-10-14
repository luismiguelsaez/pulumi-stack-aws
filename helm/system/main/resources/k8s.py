from pulumi import Output, ResourceOptions
from pulumi_kubernetes.core.v1 import ConfigMap, ConfigMapPatch
from pulumi_kubernetes.meta.v1 import ObjectMetaPatchArgs
from stack import k8s_provider
from resources import iam
from resources.helm import karpenter_helm_release
from requests import get
from tools import karpenter
from stack import eks, cluster_tags, discovery_tags, k8s_provider

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
