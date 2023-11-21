from pulumi_aws.ssm import Parameter
from pulumi_aws.secretsmanager import Secret, SecretVersion
import pulumi
from resources import iam
from stack import eks


param_eks_cluster_prefix = eks.get_output('eks_cluster_name')

roles_system_secret = Secret(
    resource_name=f"eks-cluster-iam-roles",
    name=pulumi.Output.concat("/eks/cluster/", param_eks_cluster_prefix, "/iam/roles"),
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
