from pulumi import StackReference, get_stack, get_project, Config

aws_config = Config("aws")
network_config = Config("network")

org = Config().require("org")
project = get_project()
env = get_stack()

common_tags = {
    "pulumi:project": project,
    "pulumi:stack": env,
}
