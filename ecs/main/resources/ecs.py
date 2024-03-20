from resources import elb, iam
from stack import network, name_prefix, env
from pulumi_aws import ecs
import json

ecs_cluster = ecs.Cluster(
    name=name_prefix,
    resource_name=name_prefix,
    settings=[
        {
            "name": "containerInsights",
            "value": "enabled",
        }
    ],
    tags={
        "Name": name_prefix,
    },
)

ecs_cluster_capacity_providers = ecs.ClusterCapacityProviders(
    resource_name=name_prefix,
    cluster_name=ecs_cluster.name,
    capacity_providers=[
        "FARGATE_SPOT",
        "FARGATE",
    ],
    default_capacity_provider_strategies=[
        ecs.ClusterCapacityProvidersDefaultCapacityProviderStrategyArgs(
            capacity_provider="FARGATE_SPOT",
            weight=10,
        ),
        ecs.ClusterCapacityProvidersDefaultCapacityProviderStrategyArgs(
            capacity_provider="FARGATE",
            weight=1,
        )
    ],
)

ecs_cluster_service_test_task_definition_nginx = ecs.TaskDefinition(
    resource_name=f"ecs-cluster-{name_prefix}-test-nginx",
    cpu="256",
    memory="512",
    network_mode="awsvpc",
    family=f"ecs-cluster-{name_prefix}-test-nginx",
    task_role_arn=iam.iam_role_task_execution.arn,
    container_definitions=json.dumps([
        {
            "name": "nginx",
            "image": "nginx:1.25.3-alpine",
            "cpu": 10,
            "memory": 256,
            "essential": True,
            "portMappings": [
                {
                    "containerPort": 80,
                    "hostPort": 80,
                }
            ],
        },
    ]),
    tags={
        "Name": f"ecs-cluster-{name_prefix}-test",
    },
)

ecs_cluster_service_test = ecs.Service(
    resource_name=f"ecs-cluster-{name_prefix}-test",
    name=f"ecs-cluster-{name_prefix}-test",
    cluster=ecs_cluster.name,
    network_configuration=ecs.ServiceNetworkConfigurationArgs(
        assign_public_ip=False,
        subnets=network.get_output("subnets_private"),
        security_groups=[
            elb.ecs_elb_security_group.id,
        ],
    ),
    desired_count=1,
    task_definition=ecs_cluster_service_test_task_definition_nginx.arn,
    load_balancers=[
        ecs.ServiceLoadBalancerArgs(
            target_group_arn=elb.ecs_elb_target_group_test.arn,
            container_name="nginx",
            container_port=80,
        )
    ],
)
