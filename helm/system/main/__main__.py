from resources import helm, k8s, iam, secrets
from pulumi import export
import yaml
from stack import charts_config

"""
Export new `aws-auth` ConfigMap contents
"""
export("karpenter-aws-auth-cm", k8s.new_roles_obj.apply(lambda roles: yaml.dump(roles, default_flow_style=False)))
