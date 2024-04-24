from pulumi import Config, get_project, get_stack

aws_config = Config("aws")
stack_config = Config("stack")
vpc_config = Config("vpc")
eks_config = Config("eks")

org = Config().require("org")
project = get_project()
env = get_stack()

common_tags = {
    "pulumi:project": project,
    "pulumi:stack": env,
}

# VPC
discovery_tags_public = {
    "kubernetes.io/role/elb": "1",
}

discovery_tags_private = {
    "karpenter.sh/discovery": stack_config.require('name'),
    "kubernetes.io/role/internal-elb": "1",
}

# EKS
cluster_tags = {
    #f"kubernetes.io/cluster/{stack_config.require('name')}": "owned",
    "aws:eks:cluster-name": f"{stack_config.require('name')}",
}

discovery_tags = {
    "karpenter.sh/discovery": stack_config.require('name'),
}

# HELM
charts_config = Config("charts")
argocd_config = Config("argocd")
ingress_config = Config("ingress")
monitoring_config = Config("monitoring")
