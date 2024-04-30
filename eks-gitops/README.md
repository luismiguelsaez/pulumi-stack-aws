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

After the AWS CLI is configured, you can authenticate with the following command:

```bash
aws sso login --sso-session default
```

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

## Cluster cleanup

### Karpenter nodes

After cluster removal, there could be some Karpenter nodes still running, so we would need to remove them

```bash
export AWS_PAGER=""
IDS=($(aws --profile dev ec2 describe-instances --filter "Name=tag:karpenter.sh/managed-by,Values=main" --query 'Reservations[].Instances[].[InstanceId]' --output text | tr '\n' ' '))

for ID in ${IDS[@]}; do echo "Deleting instance $ID"; aws --profile dev ec2 terminate-instances --instance-ids "$ID"; done
```

### Load balancers

Find load balancers that could have been created from the aws-load-balancer-controller and left after the cluster removal

```bash
aws --profile dev elbv2 describe-load-balancers | jq -r '.LoadBalancers[].LoadBalancerArn' | while read ARN; do echo $ARN; aws --profile dev elbv2 describe-tags --resource-arns $ARN | jq -r '.TagDescriptions[0].Tags[]|select(.Key == "elbv2.k8s.aws/cluster" and .Value == "main")'; done

TG_ARNS=$(aws --profile dev elbv2 describe-target-groups | jq -r '.TargetGroups[]|select(.LoadBalancerArns|length == 0)|.TargetGroupArn')
for ARN in ${TG_ARNS[@]}; do echo "Deleting TG $ID"; aws --profile dev elbv2 delete-target-group --target-group-arn "$ARN"; done
```