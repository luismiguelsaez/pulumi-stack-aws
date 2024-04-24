from pulumi import Config, get_project, get_stack

aws_config = Config("aws")
stack_config = Config("stack")
vpc_config = Config("vpc")

org = Config().require("org")
project = get_project()
env = get_stack()

common_tags = {
    "pulumi:project": project,
    "pulumi:stack": env,
}

discovery_tags_public = {
    "kubernetes.io/role/elb": "1",
}

discovery_tags_private = {
    "karpenter.sh/discovery": stack_config.require('name'),
    "kubernetes.io/role/internal-elb": "1",
}
