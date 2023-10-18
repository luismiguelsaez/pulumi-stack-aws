from pulumi import ResourceOptions
from pulumi_kubernetes.helm.v3 import Release, RepositoryOptsArgs
from resources import iam
from stack import aws_config, charts_config, network, eks, k8s_provider

"""
Deploy Cluster Autoscaler Helm chart
"""
if charts_config.require_bool("cluster_autoscaler_enabled"):
    cluster_autoscaler_helm_release = Release(
        "cluster-autoscaler-helm-release",
        repository_opts=RepositoryOptsArgs(
            repo="https://kubernetes.github.io/autoscaler"
        ),
        version=charts_config.require("cluster_autoscaler_version"),
        chart="cluster-autoscaler",
        namespace=charts_config.require("cluster_autoscaler_namespace"),
        create_namespace=True,
        name="cluster-autoscaler",
        values={
            "autoDiscovery": {
                "clusterName": eks.get_output("eks_cluster_name"),
            },
            "awsRegion": aws_config.require("region"),
            "rbac": {
                "create": True,
                "serviceAccount": {
                    "create": True,
                    "annotations": {
                        "eks.amazonaws.com/role-arn": iam.cluster_autoscaler_role.arn,
                    }
                },
            },
            "extraArgs": {
                "balance-similar-node-groups": True,
                "skip-nodes-with-system-pods": False,
            },
        },
        opts=ResourceOptions(provider=k8s_provider)
    )

"""
Deploy Karpenter Helm chart
"""
if charts_config.require_bool("karpenter_enabled"):
    karpenter_helm_release = Release(
        "karpenter-helm-release",
        repository_opts=RepositoryOptsArgs(
            repo="https://charts.karpenter.sh",
        ),
        version=charts_config.require("karpenter_version"),
        chart="karpenter",
        namespace=charts_config.require("karpenter_namespace"),
        create_namespace=True,
        name="karpenter",
        values={
            "controller": {
                "logLevel": "info",
            },
            "serviceAccount": {
                "create": True,
                "annotations": {
                    "eks.amazonaws.com/role-arn": iam.karpenter_role.arn,
                }
            },
            "clusterName": eks.get_output("eks_cluster_name"),
            "clusterEndpoint": eks.get_output("eks_cluster_endpoint"),
            "aws": {
                "defaultInstanceProfile": iam.karpenter_node_role_instance_profile.name,
                "vmMemoryOverheadPercent": 0.075
            },
        },
        opts=ResourceOptions(provider=k8s_provider, depends_on=[cluster_autoscaler_helm_release])
    )

"""
Deploy AWS Load Balancer Controller Helm chart
"""
if charts_config.require_bool("aws_load_balancer_controller_enabled"):
    aws_load_balancer_controller_release = Release(
        "aws-load-balancer-controller-helm-release",
        repository_opts=RepositoryOptsArgs(
            repo="https://aws.github.io/eks-charts",
        ),
        version=charts_config.require("aws_load_balancer_controller_version"),
        chart="aws-load-balancer-controller",
        namespace=charts_config.require("aws_load_balancer_controller_namespace"),
        create_namespace=True,
        name="aws-load-balancer-controller",
        values={
            "clusterName": eks.get_output("eks_cluster_name"),
            "region": aws_config.require("region"),
            "vpcId": network.get_output("vpc_id"),
            "serviceAccount": {
                "create": True,
                "annotations": {
                    "eks.amazonaws.com/role-arn": iam.aws_load_balancer_controller_role.arn,
                }
            },
        },
        opts=ResourceOptions(
            provider=k8s_provider,
            depends_on=[karpenter_helm_release, cluster_autoscaler_helm_release],
            ignore_changes=["checksum"]
        )
    )

"""
Deploy AWS EBS CSI Driver Helm chart
"""
if charts_config.require_bool("ebs_csi_driver_enabled"):
    ebs_csi_driver_release = Release(
        "ebs-csi-driver-helm-release",
        repository_opts=RepositoryOptsArgs(
            repo="https://kubernetes-sigs.github.io/aws-ebs-csi-driver",
        ),
        version=charts_config.require("ebs_csi_driver_version"),
        chart="aws-ebs-csi-driver",
        namespace=charts_config.require("ebs_csi_driver_namespace"),
        create_namespace=True,
        name="aws-ebs-csi-driver",
        values={
            "storageClasses": [
                {
                    "name": "ebs",
                    "annotations": {
                        "storageclass.kubernetes.io/is-default-class": "true",
                    },
                    "labels": {},
                    "volumeBindingMode": "WaitForFirstConsumer",
                    "reclaimPolicy": "Retain",
                    "allowVolumeExpansion": True,
                    "parameters": {
                        "encrypted": "true",
                    },
                }
            ],
            "controller": {
                "serviceAccount": {
                    "create": True,
                    "annotations": {
                        "eks.amazonaws.com/role-arn": iam.ebs_csi_driver_role.arn,
                    },
                }
            },
            "node": {
                "serviceAccount": {
                    "create": True,
                    "annotations": {
                        "eks.amazonaws.com/role-arn": iam.ebs_csi_driver_role.arn,
                    },
                }
            },
        },
        opts=ResourceOptions(provider=k8s_provider, depends_on=[karpenter_helm_release, cluster_autoscaler_helm_release])
    )

"""
Deploy AWS EBS CSI Driver Helm chart
"""
if charts_config.require_bool("external_dns_enabled"):
    external_dns_release = Release(
        "external-dns-helm-release",
        repository_opts=RepositoryOptsArgs(
            repo="https://kubernetes-sigs.github.io/external-dns",
        ),
        version=charts_config.require("external_dns_version"),
        chart="external-dns",
        namespace=charts_config.require("external_dns_namespace"),
        name="external-dns",
        create_namespace=True,
        values={
            "provider": "aws",
            "sources": ["service", "ingress"],
            "policy": "sync",
            "deploymentStrategy": {
                "type": "Recreate",
            },
            "serviceAccount": {
                "create": True,
                "annotations": {
                    "eks.amazonaws.com/role-arn": iam.external_dns_role.arn,
                },
            }
        },
        opts=ResourceOptions(provider=k8s_provider, depends_on=[karpenter_helm_release, cluster_autoscaler_helm_release])
    )
