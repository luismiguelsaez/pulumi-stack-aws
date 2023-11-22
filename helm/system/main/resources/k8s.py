from pulumi import Output, ResourceOptions
from pulumi_kubernetes.core.v1 import ConfigMap, ConfigMapPatch
from pulumi_kubernetes.meta.v1 import ObjectMetaPatchArgs
from stack import k8s_provider
from resources import iam
from requests import get
from tools import karpenter
from stack import eks, cluster_tags, discovery_tags, k8s_provider, charts_config
import yaml

"""
Setup aws-auth ConfigMap for Karpenter
"""
aws_auth_cm = ConfigMap.get(
    "aws-auth",
    id="kube-system/aws-auth",
    opts=ResourceOptions(provider=k8s_provider)
)

roles_obj = aws_auth_cm.data['mapRoles'].apply(lambda roles: yaml.load(roles, Loader=yaml.Loader))

new_roles_obj = Output.all(
    roles_obj,
    iam.karpenter_node_role.arn
).apply(lambda args:
    args[0] + [
        {
            "rolearn": args[1],
            "username": f"system:node:{{{{EC2PrivateDNSName}}}}",
            "groups": [
                "system:bootstrappers",
                "system:nodes"
            ]
        }
    ] if len(list(filter(lambda o: o["rolearn"] == args[1], args[0]))) < 1 else args[0]
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
        }
    ),
    data={
        "mapRoles": new_roles_obj.apply(lambda roles: yaml.dump(roles, default_flow_style=False))
    },
    opts=ResourceOptions(provider=k8s_provider, retain_on_delete=True)
)

"""
Provision Karpenter AWSNodetemplates
"""
if charts_config.require_bool("karpenter_enabled"):

    public_ssh_key = get("https://github.com/luismiguelsaez.keys").text.strip()

    from resources.helm import karpenter_helm_release

    Output.all(
        iam.karpenter_node_role_instance_profile.name
    ).apply(lambda args:
        karpenter.karpenter_templates(
            name="karpenter-aws-node-templates",
            provider=k8s_provider,
            manifests_path="resources/nodetemplates",
            ssh_public_key=public_ssh_key,
            instance_profile=args[0],
            sg_selector_tags=cluster_tags,
            subnet_selector_tags=discovery_tags,
            eks_cluster_security_group_id=eks.get_output("eks_cluster_security_group_id"),
            depends_on=[karpenter_helm_release]
        )
    )
