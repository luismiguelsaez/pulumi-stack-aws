from pulumi import StackReference, get_stack, get_project, Config

ecs_config = Config("ecs")
aws_config = Config("aws")

org = Config().require("org")
project = get_project()
env = get_stack()

name_prefix = ecs_config.require("name_prefix")
networking_mode = ecs_config.require("networking_mode")

"""
Stack references
"""
network = StackReference(f"{org}/network-{name_prefix}/{env}")
