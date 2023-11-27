from pulumi import ResourceOptions, Output
from pulumi_kubernetes.helm.v3 import Release, RepositoryOptsArgs
from resources import iam, secrets
from stack import env, aws_config, charts_config, ebs_csi_driver_config, ingress_config, opensearch_config, argocd_config, network, eks, k8s_provider, name_prefix
from python_pulumi_helm import releases

"""
Deploy Cluster Autoscaler Helm chart
"""
if charts_config.require_bool("cluster_autoscaler_enabled"):
    cluster_autoscaler_helm_release = Release(
        "cluster-autoscaler",
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
        resource_name="karpenter",
        name="karpenter",
        chart="oci://public.ecr.aws/karpenter/karpenter",
        version=charts_config.require("karpenter_version"),
        namespace=charts_config.require("karpenter_namespace"),
        create_namespace=True,
        values={
            "controller": {
                "resources": {
                    "requests": {
                        "cpu": "1",
                        "memory": "1Gi",
                    },
                    "limits": {
                        "cpu": "1",
                        "memory": "1Gi",
                    },
                },
            },
            "serviceAccount": {
                "create": True,
                "annotations": {
                    "eks.amazonaws.com/role-arn": iam.karpenter_role.arn,
                }
            },
            # Versions up to v0.31.x
            #"aws": {
            #    "clusterName": eks.get_output("eks_cluster_name"),
            #    "clusterEndpoint": eks.get_output("eks_cluster_endpoint"),
            #},
            "settings": {
                # Version v0.32.x and above
                "clusterName": eks.get_output("eks_cluster_name"),
                "clusterEndpoint": eks.get_output("eks_cluster_endpoint"),
                "vmMemoryOverheadPercent": 0.075,
                #"defaultInstanceProfile": iam.karpenter_node_role_instance_profile.name,
                #"assumeRoleARN": iam.karpenter_role.arn,
            },
        },
        opts=ResourceOptions(provider=k8s_provider, depends_on=[cluster_autoscaler_helm_release])
    )

"""
Deploy AWS Load Balancer Controller Helm chart
"""
if charts_config.require_bool("aws_load_balancer_controller_enabled"):
    aws_load_balancer_controller_release = Release(
        resource_name="aws-load-balancer-controller",
        name="aws-load-balancer-controller",
        repository_opts=RepositoryOptsArgs(
            repo="https://aws.github.io/eks-charts",
        ),
        version=charts_config.require("aws_load_balancer_controller_version"),
        chart="aws-load-balancer-controller",
        namespace=charts_config.require("aws_load_balancer_controller_namespace"),
        create_namespace=True,
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
        resource_name="ebs-csi-driver",
        name="aws-ebs-csi-driver",
        repository_opts=RepositoryOptsArgs(
            repo="https://kubernetes-sigs.github.io/aws-ebs-csi-driver",
        ),
        version=charts_config.require("ebs_csi_driver_version"),
        chart="aws-ebs-csi-driver",
        namespace=charts_config.require("ebs_csi_driver_namespace"),
        create_namespace=True,
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
        resource_name="external-dns",
        name="external-dns",
        repository_opts=RepositoryOptsArgs(
            repo="https://kubernetes-sigs.github.io/external-dns",
        ),
        version=charts_config.require("external_dns_version"),
        chart="external-dns",
        namespace=charts_config.require("external_dns_namespace"),
        create_namespace=True,
        values={
            "provider": "aws",
            "sources": ["service", "ingress"],
            "policy": "sync",
            "deploymentStrategy": {
                "type": "Recreate",
            },
            "txtOwnerId": Output.concat("external-dns-", eks.get_output("eks_cluster_name")), 
            "txtSuffix": "",
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
    # Minimal ArgoCD Helm chart for cluster bootstrapping
    helm_argocd_chart = Release(
        resource_name="argo-cd",
        name="argo-cd",
        repository_opts=RepositoryOptsArgs(
            repo="https://argoproj.github.io/argo-helm",
        ),
        version=charts_config.require("argocd_version"),
        chart="argo-cd",
        namespace=charts_config.require("argocd_namespace"),
        create_namespace=True,
        force_update=True,
        max_history=4,
        skip_await=True,
        timeout=300,
        values={
            "crds": {
                "install": True,
                "keep": False,
                "annotations": {},
                "additionalLabels": {},
            },
            "global": {
                "additionalLabels": {
                    "app": "argo-cd"
                },
            },
            "configs": {
                "cm": {
                    "url": f"{argocd_config.require('ingress_protocol')}://{argocd_config.require('ingress_hostname')}",
                    "exec.enabled": "true",
                    "admin.enabled": "true",
                    "timeout.reconciliation": "180s",
                    "resource.customizations": "argoproj.io/Application:\n  health.lua: |\n    hs = {}\n    hs.status = \"Progressing\"\n    hs.message = \"\"\n    if obj.status ~= nil then\n      if obj.status.health ~= nil then\n        hs.status = obj.status.health.status\n        if obj.status.health.message ~= nil then\n          hs.message = obj.status.health.message\n        end\n      end\n    end\n    return hs\n",
                },
                "params": {
                    "server.insecure": "true",
                    "server.disable.auth": "false",
                },
            },
            "server": {
                "ingress": {
                    "enabled": "true",
                    "ingressClassName": "", #argocd_config.require("ingress_class_name"),
                    "hosts": [ argocd_config.require("ingress_hostname") ],
                    "paths": [ "/" ],
                    "pathType": "Prefix",
                },
            },
            "repoServer": {
                "serviceAccount": {
                    "create": "true",
                    "annotations": {
                        "eks.amazonaws.com/role-arn": iam.argocd_role.arn,
                        "automountServiceAccountToken": "true",
                    },
                },
                # CMP BEGIN
                "volumes": [
                    {
                        "name": "cmp-kustomize-aws-secretsmanager",
                        "configMap": {
                            "name": "cmp-kustomize-aws-secretsmanager"
                        }
                    },
                    {
                        "name": "cmp-tmp",
                        "emptyDir": {}
                    }
                ],
                "extraContainers": [
                    {
                        "name": "cmp-kustomize-aws-secretsmanager",
                        "command": [
                            "/var/run/argocd/argocd-cmp-server"
                        ],
                        "args": [
                            "--loglevel",
                            "debug",
                            "--logformat",
                            "json"
                        ],
                        "image": "luismiguelsaez/argocd-cmp-default:v0.0.2",
                        "securityContext": {
                            "runAsNonRoot": True,
                            "runAsUser": 999,
                            "runAsGroup": 999
                        },
                        "volumeMounts": [
                            {
                                "mountPath": "/var/run/argocd",
                                "name": "var-files"
                            },
                            {
                                "mountPath": "/home/argocd/cmp-server/plugins",
                                "name": "plugins"
                            },
                            {
                                "mountPath": "/home/argocd/cmp-server/config/plugin.yaml",
                                "subPath": "plugin.yaml",
                                "name": "cmp-kustomize-aws-secretsmanager"
                            },
                            {
                                "mountPath": "/tmp",
                                "name": "cmp-tmp"
                            }
                        ],
                        "env": [
                            {
                                "name": "AVP_TYPE",
                                "value": "awssecretsmanager"
                            },
                            {
                                "name": "HOME",
                                "value": "/tmp"
                            }
                        ]
                    }
                ],
                ## CMP END
            },
            "extraObjects": [
                # AWS Secrets Manager plugin, required for root Application bootstrap
                {
                    "apiVersion": "v1",
                    "kind": "ConfigMap",
                    "metadata": {
                        "name": "cmp-kustomize-aws-secretsmanager"
                    },
                    "data": {
                        "plugin.yaml": "apiVersion: argoproj.io/v1alpha1\nkind: ConfigManagementPlugin\nmetadata:\n  name: cmp-kustomize-aws-secretsmanager\nspec:\n  version: v1.0\n  init:\n    command: [sh, -c]\n    args:\n      - |\n        find . -type f -name kustomization.yaml\n  generate:\n    command: [sh, -c]\n    args:\n      - |\n        kustomize build . | argocd-vault-plugin generate --verbose-sensitive-output -\n  discover:\n    find:\n      glob: \"./**/kustomization.yaml\"\n"
                    }
                }
            ],
        },
        opts=ResourceOptions(provider=k8s_provider, depends_on=[secrets.cluster_info_secret, secrets.roles_system_secret, secrets.ingress_secret])
    )

cluster_gitops_path = Output.concat("clusters/", env, "/", eks.get_output("eks_cluster_name"))

if charts_config.require_bool("argocd_apps_enabled"):
    helm_argocd_apps_chart = Release(
        resource_name="argocd-apps",
        name="argocd-apps",
        repository_opts=RepositoryOptsArgs(
            repo="https://argoproj.github.io/argo-helm",
        ),
        version=charts_config.require("argocd_apps_version"),
        chart="argocd-apps",
        namespace=charts_config.require("argocd_apps_namespace"),
        create_namespace=True,
        force_update=True,
        max_history=4,
        skip_await=True,
        timeout=300,
        opts=ResourceOptions(provider=k8s_provider, depends_on=[helm_argocd_chart]),
        values={
            "applications": [
                {
                    "name": "root",
                    "namespace": "argocd",
                    "additionalLabels": {},
                    "additionalAnnotations": {},
                    "finalizers": [
                        "resources-finalizer.argocd.argoproj.io" 
                    ],
                    "project": "default",
                    "source": {
                        "repoURL": "https://github.com/luismiguelsaez/gitops-argocd-self-managed",
                        "targetRevision": "HEAD",
                        "path": cluster_gitops_path,
                        "plugin": {}, # Uses plugin auto-discovery
                    },
                    "destination": {
                        "server": "https://kubernetes.default.svc",
                        "namespace": "argocd"
                    },
                    "syncPolicy": {
                        "automated": {
                            "prune": True,
                            "selfHeal": True
                        },
                        "syncOptions": [
                            "Validate=true",
                            "CreateNamespace=true",
                            "RespectIgnoreDifferences=true",
                        ],
                        "retry": {
                            "limit": 10,
                            "backoff": {
                                "duration": "5s",
                                "factor": 2,
                                "maxDuration": "2m"
                            }
                        }
                    },
                    "revisionHistoryLimit": 10,
                    "ignoreDifferences": [],
                },
            ],
        }
    )
