from pulumi import get_project, get_stack

project = get_project()
env = get_stack()

"""
Set common tags
"""
common_tags = {
    "pulumi:project": project,
    "pulumi:stack": env,
}
