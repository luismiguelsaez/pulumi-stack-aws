from pulumi import StackReference, get_stack, get_project, Config

ec2_config = Config("ec2")
aws_config = Config("aws")

org = Config().require("org")
project = get_project()
env = get_stack()

name_prefix = ec2_config.require("name_prefix")

"""
Stack references
"""
network = StackReference(f"{org}/network-{name_prefix}/{env}")
