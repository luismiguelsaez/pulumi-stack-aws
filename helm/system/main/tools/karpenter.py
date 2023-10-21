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
    eks_cluster_name: Output,
    ssh_public_key: str,
    sg_selector_tags: dict = {},
    subnet_selector_tags: dict = {},
    depends_on: list = []
  ):

    def transform_manifest(obj, opts):
        sg_selector=sg_selector_tags
        subnet_selector=subnet_selector_tags

        obj['spec']['securityGroupSelector'] = sg_selector
        obj['spec']['subnetSelector'] = subnet_selector

    files_jinja = [
        path.join(path.dirname("__file__"), file) for file in glob.glob(path.join(path.dirname("__file__"), manifests_path, "*.j2"))
    ]
    
    for file in files_jinja:
      with open(file, 'r') as f:
        file_contents = f.read()
        rendered_file = jinja2.Template(file_contents).render(
          ssh_public_key=ssh_public_key,
          sg_selector_tags=sg_selector_tags,
          subnet_selector_tags=subnet_selector_tags,
        )
      with open(file.replace(".j2", ".yaml"), 'w') as f:
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
          transformations=[transform_manifest],
          opts=resource_options
        )
      )

    return config_files
