from pulumi_kubernetes.yaml import ConfigFile
from pulumi_kubernetes import Provider
from pulumi import ResourceOptions, Output
from os import path
import glob

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
        #{
        #    "karpenter.sh/discovery": eks_cluster_name.apply(lambda name: name)
        #}

        subnet_selector=subnet_selector_tags
        #{
        #    "karpenter.sh/discovery": eks_cluster_name.apply(lambda name: name)
        #}

        obj['spec']['securityGroupSelector'] = sg_selector
        obj['spec']['subnetSelector'] = subnet_selector
        
        #obj['spec']['userData'] = ""

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
