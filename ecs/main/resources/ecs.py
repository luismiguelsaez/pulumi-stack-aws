from resources import elb
from stack import network, name_prefix, env
from pulumi_aws import ecs

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

ecs_cluster_service_test = ecs.Service(
    resource_name=f"ecs-cluster-{name_prefix}-test",
    name=f"ecs-cluster-{name_prefix}-test",
    cluster=ecs_cluster.name,
    desired_count=1,
    load_balancers=[
        ecs.ServiceLoadBalancerArgs(
            target_group_arn=elb.ecs_elb_target_group_test.arn,
            container_name="test",
            container_port=80,
        )
    ],
)
