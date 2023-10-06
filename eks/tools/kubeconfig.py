import pulumi
from pulumi_aws.eks import Cluster

def create_kubeconfig(eks_cluster: Cluster, region: pulumi.Input[str]):
    
    kubeconfig_yaml = pulumi.Output.all(eks_cluster.name, eks_cluster.endpoint, eks_cluster.certificate_authority).apply(lambda o: f"""
apiVersion: v1
kind: Config
current-context: {o[0]}
preferences:
colors: true
clusters:
- name: {o[0]}
    cluster:
    api-version: v1
    server: {o[1]}
    certificate-authority-data: {o[2]['data']}
contexts:
- name: {o[0]}
    context:
    cluster: {o[0]}
    namespace: default
    user: aws
users:
    - name: aws
        user:
        exec:
            apiVersion: client.authentication.k8s.io/v1beta1
            command: aws
            args:
                - --region
                - {region}
                - eks
                - get-token
                - --cluster-name
                - {o[0]}
                - --output
                - json
""")

    return kubeconfig_yaml
