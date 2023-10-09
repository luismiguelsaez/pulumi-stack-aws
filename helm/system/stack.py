from pulumi import StackReference, get_stack, get_project, Config

aws_config = Config("aws")
helm_config = Config("helm")
charts_config = Config("charts")

org = Config().require("org")
project = get_project()
env = get_stack()

name_prefix = helm_config.require("name_prefix")

common_tags = {
    "pulumi:project": project,
    "pulumi:stack": env,
}

"""
Stack references
"""
eks = StackReference(f"{org}/eks-main/{env}")
