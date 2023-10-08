from pulumi import StackReference, get_stack, Config

aws_config = Config("aws")
helm_config = Config("helm")
charts_config = Config("charts")

org = Config().require("org")
env = get_stack()

"""
Stack references
"""
eks = StackReference(f"{org}/eks-main/{env}")
