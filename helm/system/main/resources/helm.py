from pulumi import ResourceOptions
from pulumi_kubernetes.helm.v3 import Release, RepositoryOptsArgs
from resources import iam
from stack import aws_config, charts_config, ebs_csi_driver_config, ingress_config, opensearch_config, argocd_config, network, eks, k8s_provider, name_prefix
from python_pulumi_helm import releases

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
Deploy Metrics Server Helm chart
"""
if charts_config.require_bool("metrics_server_enabled"):
    helm_metrics_server_chart = releases.metrics_server(
        provider=k8s_provider,
        depends_on=[]
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
        opts=ResourceOptions(provider=k8s_provider, depends_on=[])
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
                    "name": ebs_csi_driver_config.require("storage_class_name"),
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
Deploy External DNS Helm chart
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

"""
Deploy Ingress Nginx controllers
"""
if charts_config.require_bool("ingress_nginx_external_enabled"):
    helm_ingress_nginx_external_chart = releases.ingress_nginx(
        version=charts_config.require("ingress_nginx_external_version"),
        name="ingress-nginx-internet-facing",
        name_suffix="external",
        public=True,
        ssl_enabled=ingress_config.require_bool("external_ssl_enabled"),
        acm_cert_arns=ingress_config.require("external_ssl_cert_arns").split(","),
        alb_resource_tags={ "eks-cluster-name": name_prefix, "ingress-name": "ingress-nginx-internet-facing" },
        metrics_enabled=False,
        global_rate_limit_enabled=False,
        karpenter_node_enabled=False,
        provider=k8s_provider,
        namespace=charts_config.require("ingress_nginx_external_namespace"),
        depends_on=[karpenter_helm_release, cluster_autoscaler_helm_release, aws_load_balancer_controller_release]
    )

if charts_config.require_bool("ingress_nginx_internal_enabled"):
    helm_ingress_nginx_external_chart = releases.ingress_nginx(
        version=charts_config.require("ingress_nginx_internal_version"),
        name="ingress-nginx-internal",
        name_suffix="internal",
        public=False,
        ssl_enabled=ingress_config.require_bool("external_ssl_enabled"),
        acm_cert_arns=[],
        alb_resource_tags={ "eks-cluster-name": name_prefix, "ingress-name": "ingress-nginx-internal" },
        metrics_enabled=False,
        global_rate_limit_enabled=False,
        karpenter_node_enabled=False,
        provider=k8s_provider,
        namespace=charts_config.require("ingress_nginx_internal_namespace"),
        depends_on=[karpenter_helm_release, cluster_autoscaler_helm_release, aws_load_balancer_controller_release]
    )

if charts_config.require_bool("opensearch_enabled"):
    helm_opensearch_chart = releases.opensearch(
        version=charts_config.require("opensearch_version"),
        ingress_domain="dev.lokalise.cloud",
        ingress_class_name="nginx-internal",
        storage_class_name=ebs_csi_driver_config.require("storage_class_name"),
        storage_size=opensearch_config.require("storage_size"),
        replicas=opensearch_config.require_int("storage_size"),
        karpenter_node_enabled=True,
        karpenter_node_provider_name="bottlerocket-default",
        resources_requests_memory_mb=opensearch_config.require("memory_mb"),
        resources_requests_cpu=opensearch_config.require("cpu"),
        provider=k8s_provider,
        namespace=charts_config.require("opensearch_namespace"),
        depends_on=[karpenter_helm_release, cluster_autoscaler_helm_release, ebs_csi_driver_release, helm_ingress_nginx_external_chart]
    )


if charts_config.require_bool("argocd_enabled"):
    helm_argocd_chart = releases.argocd(
        version=charts_config.require("argocd_version"),
        provider=k8s_provider,
        namespace=charts_config.require("argocd_namespace"),
        depends_on=[karpenter_helm_release, helm_ingress_nginx_external_chart],
        ingress_hostname=argocd_config.require("ingress_hostname"),
        ingress_protocol=argocd_config.require("ingress_protocol"),
        ingress_class_name=argocd_config.require("ingress_class_name"),
        argocd_redis_ha_enabled=argocd_config.require_bool("redis_ha_enabled"),
        argocd_redis_ha_storage_class=ebs_csi_driver_config.require("storage_class_name"),
        argocd_redis_ha_storage_size=argocd_config.require("redis_ha_storage_size"),
        argocd_redis_ha_haproxy_enabled=True,
        argocd_application_controller_replicas=argocd_config.require_int("controller_replicas"),
        argocd_applicationset_controller_replicas=argocd_config.require_int("applicationset_replicas"),
        karpenter_node_enabled=True,
        karpenter_node_provider_name="bottlerocket-default",
        karpenter_provisioner_controller_instance_category=["t"],
        karpenter_provisioner_controller_instance_arch=["arm64"],
        karpenter_provisioner_controller_instance_capacity_type=["spot"],
        karpenter_provisioner_redis_instance_category=["t"],
        karpenter_provisioner_redis_instance_arch=["arm64"],
        karpenter_provisioner_redis_instance_capacity_type=["spot"],
        controller_resources=argocd_config.require_object("controller_resources"),
        repo_server_resources=argocd_config.require_object("repo_server_resources"),
    )
