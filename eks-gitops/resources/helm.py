from pulumi import ResourceOptions, Output
from pulumi_kubernetes.helm.v3 import Release, RepositoryOptsArgs
from pulumi_kubernetes import Provider
from resources import secrets
from . import eks
from . import iam_helm as iam
from tools.kubeconfig import create_kubeconfig
from common import aws_config, env, charts_config, argocd_config

aws_region = aws_config.require("region")

k8s_provider = Provider(
    resource_name="k8s",
    kubeconfig=create_kubeconfig(eks_cluster=eks.eks_cluster, region=aws_region, aws_profile=env),
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
        skip_await=False,
        timeout=300,
        opts=ResourceOptions(
            provider=k8s_provider,
            depends_on=secrets.secrets
        ),
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
                    # Uncomment for app-of-apps pattern
                    #"resource.customizations": "argoproj.io/Application:\n  health.lua: |\n    hs = {}\n    hs.status = \"Progressing\"\n    hs.message = \"\"\n    if obj.status ~= nil then\n      if obj.status.health ~= nil then\n        hs.status = obj.status.health.status\n        if obj.status.health.message ~= nil then\n          hs.message = obj.status.health.message\n        end\n      end\n    end\n    return hs\n",
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
                        "name": "cmp-helm-aws-secretsmanager",
                        "configMap": {
                            "name": "cmp-helm-aws-secretsmanager"
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
                        "image": "luismiguelsaez/argocd-cmp-default:v0.0.3",
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
                    },
                    {
                        "name": "cmp-helm-aws-secretsmanager",
                        "command": [
                            "/var/run/argocd/argocd-cmp-server"
                        ],
                        "args": [
                            "--loglevel",
                            "debug",
                            "--logformat",
                            "json"
                        ],
                        "image": "luismiguelsaez/argocd-cmp-default:v0.0.3",
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
                                "name": "cmp-helm-aws-secretsmanager"
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
                },
                {
                    "apiVersion": "v1",
                    "kind": "ConfigMap",
                    "metadata": {
                        "name": "cmp-helm-aws-secretsmanager"
                    },
                    "data": {
                        "plugin.yaml": "apiVersion: argoproj.io/v1alpha1\nkind: ConfigManagementPlugin\nmetadata:\n  name: cmp-helm-aws-secretsmanager\nspec:\n  version: v1.0\n  init:\n    command: [/bin/bash, -c]\n    args:\n      - |\n        # Create Helm config directory\n        mkdir -p ./.helm/config\n        mkdir -p ./.helm/cache\n        export HELM_CONFIG_HOME=./.helm/config\n        export XDG_CACHE_HOME=./.helm/cache\n        # Add Helm repos\n        helm_repos=$(helm dependencies list | awk 'NR > 1 && $0 != \"\" && $3 != \"unpacked\" {print $3}' | sort | uniq);\n        for repo in $helm_repos; do [ -n \"$repo\" ] && helm repo add $RANDOM $repo;done\n        # Fix for OCI charts\n        [ -f Chart.lock ] && rm Chart.lock\n        # Build Helm dependencies\n        helm dependency build --skip-refresh\n  generate:\n    command: [/bin/bash, -c]\n    args:\n      - |\n        export HELM_CONFIG_HOME=./.helm/config\n        export XDG_CACHE_HOME=./.helm/cache\n        export HELM_INCLUDE_CRDS=\"--include-crds\";\n        export HELM_EXTRA_PARAMS=\"\";\n        if [ -n \"$ARGOCD_ENV_HELM_SKIP_CRDS\" ]; then\n          export HELM_INCLUDE_CRDS=\"\";\n        fi;\n        if [ -n \"$ARGOCD_ENV_HELM_EXTRA_PARAMS\" ]; then\n          export HELM_EXTRA_PARAMS=\"$ARGOCD_ENV_HELM_EXTRA_PARAMS\";\n        fi;\n        echo \"$ARGOCD_ENV_HELM_VALUES\" > values-env.yaml;\n        echo \"$ARGOCD_ENV_HELM_VALUES_OVERRIDE\" > values-env-override.yaml;\n        helm template $ARGOCD_APP_NAME $HELM_INCLUDE_CRDS $HELM_EXTRA_PARAMS -n $ARGOCD_APP_NAMESPACE -f values-env.yaml -f values-env-override.yaml . |\\\n        argocd-vault-plugin generate - --verbose-sensitive-output\n  discover:\n    find:\n      glob: \"./**/Chart.yaml\"\n"
                    }
                }
            ],
        },
    )

cluster_gitops_path = Output.concat("clusters/", env, "/", eks.eks_cluster.name)

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
        skip_await=False,
        timeout=900,
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
