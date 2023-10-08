from pulumi import StackReference, get_stack, Config

eks_config = Config("eks")
aws_config = Config("aws")

org = Config().require("org")
env = get_stack()

"""
Stack references
"""
network = StackReference(f"{org}/network-main/{env}")
