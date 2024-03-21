from pulumi_aws.secretsmanager import Secret, SecretVersion, get_secret
import pulumi
from resources import iam
from stack import eks, aws_config, ingress_config, monitoring_config
from requests import get
from pulumi_aws.eks import get_cluster

"""
Create secrets to share info with ArgoCD
Secrets are retrieved later during ArgoCD bootstrap using `argocd-vault-plugin` and placeholders
"""

# Get EKS cluster info
param_eks_cluster_name = eks.get_output('eks_cluster_name')
param_eks_cluster_endpoint = eks.get_output('eks_cluster_endpoint')
param_eks_cluster_ca_data = eks.get_output('eks_cluster_ca_data')
param_eks_cluster_region = aws_config.require("region")
param_eks_cluster_security_group = get_cluster(name=param_eks_cluster_name).vpc_config.cluster_security_group_id

secrets_root_path = pulumi.Output.concat("/eks/cluster/", param_eks_cluster_name)

public_ssh_key = get("https://github.com/luismiguelsaez.keys").text.strip()


secrets_data = {
    'iam-roles': {
        'path': pulumi.Output.concat(secrets_root_path, "/iam/roles"),
        'values': {
            'karpenter': iam.karpenter_role.arn,
            'cluster_autoscaler': iam.cluster_autoscaler_role.arn,
            'aws_load_balancer_controller': iam.aws_load_balancer_controller_role.arn,
            'ebs_csi_driver': iam.ebs_csi_driver_role.arn,
            'external_dns': iam.external_dns_role.arn,
            'argocd': iam.argocd_role.arn,
        },
    },
    'info': {
        'path': pulumi.Output.concat(secrets_root_path, "/details"),
        'values': {
            'name': param_eks_cluster_name,
            'endpoint': param_eks_cluster_endpoint,
            'ca_data': param_eks_cluster_ca_data,
            'region': param_eks_cluster_region,
            'security_group': param_eks_cluster_security_group,
            'ssh_public_key': public_ssh_key,
        },
    },
    'ingress': {
        'path': pulumi.Output.concat(secrets_root_path, "/ingress"),
        'values': {
            'external_domain': ingress_config.require("external_domain"),
            'external_ssl_cert_arns': ingress_config.require("external_ssl_cert_arns"),
            'internal_domain': ingress_config.require("internal_domain"),
            'internal_ssl_cert_arns': ingress_config.require("internal_ssl_cert_arns"),
        },
    },
    'monitoring': {
        'path': pulumi.Output.concat(secrets_root_path, "/monitoring"),
        'values': {
            'pixie_deploy_key': monitoring_config.require("pixie_deploy_key"),
        },
    },
}

secrets = []
for secret in secrets_data:
    id = ''
    
    try:
        get_secret(name=secrets_data[secret]['path'])
        id = get_secret(name=secrets_data[secret]['path']).id
    except:
        secrets.append(
            Secret(
                resource_name=f"eks-cluster-{secret}",
                name=secrets_data[secret]['path'],
                force_overwrite_replica_secret=True,
                recovery_window_in_days=0,
                opts=pulumi.ResourceOptions(retain_on_delete=True),
            )
        )

        id = secrets[-1].id

    roles_system_secret_version = SecretVersion(
        resource_name=f"eks-cluster-{secret}",
        secret_id=id,
        secret_string=pulumi.Output.json_dumps(secrets_data[secret]['values']),
        opts=pulumi.ResourceOptions(retain_on_delete=True),
    )
