from pulumi_k8s.yaml import ConfigFile
from pulumi import ResourceOptions, Provider
from os import path
import glob

def karpenter_templates(name: str, provider: Provider, manifests_path: str, eks_cluster_name: str, depends_on: list = []):

    def transform_manifest(obj, opts):
        sg_selector={
            f"kubernetes.io/cluster/{eks_cluster_name}": "owned"
        }

        subnet_selector={
            "karpenter.sh/discovery": eks_cluster_name
        }

        obj['spec']['securityGroupSelector'] = sg_selector
        obj['spec']['subnetSelector'] = subnet_selector

    files = [
        path.join(path.dirname("__file__"), file) for file in glob.glob(path.join(path.dirname("__file__"), manifests_path, "*.yaml"))
    ]

    resource_options = ResourceOptions(provider=provider, depends_on=depends_on)

    config_files = []
    for file in files:
      config_files.append(
        ConfigFile(
          name=path.basename(file),
          file=file,
          transformations=[transform_manifest],
          opts=resource_options
        )
      )

    return config_files
