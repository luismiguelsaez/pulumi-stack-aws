from pulumi import StackReference, get_stack, get_project, Config

aws_config = Config("aws")
network_config = Config("network")

org = Config().require("org")
project = get_project()
env = get_stack()

name_prefix = network_config.require("name_prefix")

vpc_cidr = network_config.require("cidr")
subnet_mask = network_config.require_int("subnet_mask")

common_tags = {
    "pulumi:project": project,
    "pulumi:stack": env,
}

discovery_tags = {
    "karpenter.sh/discovery": name_prefix,
}
