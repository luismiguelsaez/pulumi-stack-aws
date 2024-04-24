# EKS cluster managed with GitOps ( ArgoCD )

## Stack setup

Modifi settings in `Pulumi.<stack-name>.yaml` file

```bash
pulumi stack ls
pulumi stack select <stack-name>
```

## Create infra

```bash
pulumi up
```

## Get Kubeconfig

```bash
pulumi stack output eks_kubeconfig  > kubeconfig.yaml
export KUBECONFIG=$(pwd)/kubeconfig.yaml
```
