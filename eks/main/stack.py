from pulumi import StackReference, get_stack, get_project, Config

eks_config = Config("eks")
aws_config = Config("aws")

org = Config().require("org")
project = get_project()
env = get_stack()

common_tags = {
    "pulumi:project": project,
    "pulumi:stack": env,
}

"""
Stack references
"""
network = StackReference(f"{org}/network-main/{env}")
