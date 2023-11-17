from pulumi_aws.ssm import Parameter
import pulumi
from resources import iam
from stack import eks

param_eks_cluster_prefix = eks.get_output('eks_cluster_name')

for key, value in [
    ('karpenter', iam.karpenter_role.arn),
    ('cluster_autoscaler', iam.cluster_autoscaler_role.arn),
    ('aws_load_balancer_controller', iam.aws_load_balancer_controller_role.arn),
    ('ebs_csi_driver', iam.ebs_csi_driver_role.arn),
    ('external_dns', iam.external_dns_role.arn),
    ('argocd', iam.argocd_role.arn),
]:
    Parameter(
        resource_name=key,
        type='String',
        name=pulumi.Output.concat("/eks/cluster/", param_eks_cluster_prefix, "/iam/roles/", key),
        value=value,
    )
