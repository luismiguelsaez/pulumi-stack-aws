from pulumi import Output, ResourceOptions
from pulumi_kubernetes.core.v1 import ConfigMap, ConfigMapPatch
from pulumi_kubernetes.meta.v1 import ObjectMetaPatchArgs
from pulumi_kubernetes import Provider
from common import env, aws_config
from resources import iam_helm as iam
from tools.kubeconfig import create_kubeconfig
from . import eks
import yaml


aws_region = aws_config.require("region")

k8s_provider = Provider(
    resource_name="k8s",
    kubeconfig=create_kubeconfig(eks_cluster=eks.eks_cluster, region=aws_region, aws_profile=env),
)


"""
Setup aws-auth ConfigMap for Karpenter ( TODO: check cluster availability first )
"""
aws_auth_cm = ConfigMap.get(
    "aws-auth",
    id="kube-system/aws-auth",
    opts=ResourceOptions(
        provider=k8s_provider,
        depends_on=[eks.eks_cluster, eks.eks_node_group_system]
    )
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
