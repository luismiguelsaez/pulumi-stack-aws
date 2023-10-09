from pulumi import StackReference, get_stack, get_project, Config

aws_config = Config("aws")
network_config = Config("network")

org = Config().require("org")
project = get_project()
env = get_stack()

name_prefix = network_config.require("name_prefix")

common_tags = {
    "pulumi:project": project,
    "pulumi:stack": env,
}

discovery_tags = {
    "karpenter.sh/discovery": name_prefix,
}
