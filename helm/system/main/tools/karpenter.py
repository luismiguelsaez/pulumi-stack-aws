from pulumi_kubernetes.yaml import ConfigFile
from pulumi_kubernetes import Provider
from pulumi import ResourceOptions, Output
from os import path
import glob
import jinja2

def karpenter_templates(
    name: str,
    provider: Provider,
    manifests_path: str,
    ssh_public_key: str,
    eks_cluster_name: Output,
    sg_selector_tags: dict = {},
    subnet_selector_tags: dict = {},
    instance_profile: str = "default",
    eks_cluster_security_group_id: str = "",
    depends_on: list = []
  ):

    files_jinja = [
        path.join(path.dirname("__file__"), file) for file in glob.glob(path.join(path.dirname("__file__"), manifests_path, "*.j2"))
    ]

    for file in files_jinja:
      with open(file, 'r') as f:
        file_contents = f.read()
        rendered_file = eks_cluster_name.apply(lambda name:
          jinja2.Template(file_contents).render(
            ssh_public_key=ssh_public_key,
            #sg_selector_tags=sg_selector_tags,
            #subnet_selector_tags=subnet_selector_tags,
            sg_selector_tags={
              #f"kubernetes.io/cluster/{eks.get_output('eks_cluster_name')}": "owned",
              "aws:eks:cluster-name": "main",
            },
            subnet_selector_tags={
              "karpenter.sh/discovery": "main",
            },
            eks_cluster_security_group_id=eks_cluster_security_group_id,
            instance_profile=instance_profile,
          )
        )
      with open(file.replace(".j2", ".yaml"), 'w') as f:
        print(rendered_file)
        f.write(rendered_file)

    files = [
        path.join(path.dirname("__file__"), file) for file in glob.glob(path.join(path.dirname("__file__"), manifests_path, "*.yaml"))
    ]

    resource_options = ResourceOptions(provider=provider, depends_on=depends_on)

    config_files = []
    for file in files:
      config_files.append(
        ConfigFile(
          name=f"{name}-{path.basename(file)}",
          file=file,
          opts=resource_options
        )
      )

    return config_files
