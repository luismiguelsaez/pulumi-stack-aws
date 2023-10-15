from resources import helm, iam, k8s
from pulumi import export, Output
import yaml

"""
Export new `aws-auth` ConfigMap contents
"""
export("karpenter-aws-auth-cm", k8s.new_roles_obj.apply(lambda roles: yaml.dump(roles, default_flow_style=False)))

"""
Export Helm releases
"""
export("helm_release_karpenter", helm.karpenter_helm_release.status)
export("helm_release_cluster_autoscaler",helm.cluster_autoscaler_helm_release.status)
