from resources import helm, k8s, iam, ssm
from pulumi import export
import yaml
from stack import charts_config

"""
Export new `aws-auth` ConfigMap contents
"""
export("karpenter-aws-auth-cm", k8s.new_roles_obj.apply(lambda roles: yaml.dump(roles, default_flow_style=False)))

"""
Export Helm releases
"""
if charts_config.require_bool("cluster_autoscaler_enabled"):
    export("helm_release_cluster_autoscaler", helm.cluster_autoscaler_helm_release.status)
if charts_config.require_bool("karpenter_enabled"):
    export("helm_release_karpenter", helm.karpenter_helm_release.status)

"""
Export IAM roles
"""
export("iam_role_karpenter", iam.karpenter_role.arn)
export("iam_role_cluster_autoscaler", iam.cluster_autoscaler_role.arn)
export("iam_role_aws_load_balancer_controller", iam.aws_load_balancer_controller_role.arn)
export("iam_role_ebs_csi_driver", iam.ebs_csi_driver_role.arn)
export("iam_role_external_dns", iam.external_dns_role.arn)
export("iam_role_argocd", iam.argocd_role.arn)
