from pulumi import StackReference, get_stack, Config

aws_config = Config("aws")
network_config = Config("network")

org = Config().require("org")
env = get_stack()
