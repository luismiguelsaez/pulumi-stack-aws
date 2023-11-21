from pulumi_aws.secretsmanager import Secret, SecretVersion
import pulumi
from resources import iam
from stack import eks, aws_config

"""
Create secrets to share info with ArgoCD
Secrets are retrieved later during ArgoCD bootstrap using `argocd-vault-plugin` and placeholders
"""

param_eks_cluster_prefix = eks.get_output('eks_cluster_name')
param_eks_cluster_endpoint = eks.get_output('eks_cluster_endpoint')
param_eks_cluster_region = aws_config.require("region")

# Create component IAM roles secret

roles_system_secret = Secret(
    resource_name=f"eks-cluster-iam-roles",
    name=pulumi.Output.concat("/eks/cluster/", param_eks_cluster_prefix, "/iam/roles"),
    force_overwrite_replica_secret=True,
)

roles_system = {
    'karpenter': iam.karpenter_role.arn,
    'cluster_autoscaler': iam.cluster_autoscaler_role.arn,
    'aws_load_balancer_controller': iam.aws_load_balancer_controller_role.arn,
    'ebs_csi_driver': iam.ebs_csi_driver_role.arn,
    'external_dns': iam.external_dns_role.arn,
    'argocd': iam.argocd_role.arn,
}

SecretVersion(
    resource_name=f"eks-cluster-iam-roles",
    secret_id=roles_system_secret.id,
    secret_string=pulumi.Output.json_dumps(roles_system),
)

# Create cluster info secret

cluster_info_secret = Secret(
    resource_name=f"eks-cluster-info",
    name=pulumi.Output.concat("/eks/cluster/", param_eks_cluster_prefix, "/info"),
    force_overwrite_replica_secret=True,
)

cluster_info = {
    'name': param_eks_cluster_prefix,
    'endpoint': param_eks_cluster_endpoint,
    'region': param_eks_cluster_region,
}

SecretVersion(
    resource_name=f"eks-cluster-info",
    secret_id=cluster_info_secret.id,
    secret_string=pulumi.Output.json_dumps(cluster_info),
)
