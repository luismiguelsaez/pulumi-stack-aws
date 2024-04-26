# EKS cluster managed with GitOps ( ArgoCD )

This Stack depends on the [GitOps repository](https://github.com/luismiguelsaez/gitops-argocd-self-managed)

## Authentication

Authentication to AWS is done through SSO, so you need to have the AWS CLI configured with the SSO profile.

```ini
[sso-session default]
sso_start_url = https://<ID>.awsapps.com/start
sso_region = eu-central-1
sso_registration_scopes = sso:account:access

[profile dev]
sso_session = default
sso_account_id = <AWS_account_id>
sso_role_name = <SSO_role_name>
region = <AWS_region>
```

*The `profile` name must match the `config:aws:profile` setting in `Pulumi.<stack_name>.yaml`*

## Stack setup

- Modify settings in `Pulumi.<stack_name>.yaml` file

- Select stack

    ```bash
    pulumi stack ls
    pulumi stack select <stack_name>
    ```

- Create infra

    ```bash
    pulumi up
    ```

- Get Kubeconfig

    ```bash
    pulumi stack output eks_kubeconfig > kubeconfig.yaml
    export KUBECONFIG=$(pwd)/kubeconfig.yaml
    ```
