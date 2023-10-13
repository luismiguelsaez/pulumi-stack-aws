from pulumi import StackReference, get_stack, get_project, Config

eks_config = Config("eks")
aws_config = Config("aws")

org = Config().require("org")
project = get_project()
env = get_stack()

name_prefix = eks_config.require("name_prefix")
eks_version = eks_config.require("version")

common_tags = {
    "pulumi:project": project,
    "pulumi:stack": env,
}

cluster_tags = {
    f"kubernetes.io/cluster/{name_prefix}": "owned"
}

discovery_tags = {
    "karpenter.sh/discovery": name_prefix,
}

"""
Stack references
"""
network = StackReference(f"{org}/network-{name_prefix}/{env}")
