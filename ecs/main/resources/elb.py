from stack import network, name_prefix, networking_mode
from pulumi_aws.alb import LoadBalancer, Listener, TargetGroup, ListenerRule, ListenerRuleActionArgs, ListenerDefaultActionArgs, ListenerDefaultActionFixedResponseArgs, ListenerRuleConditionArgs, ListenerRuleConditionHttpHeaderArgs
from pulumi_aws.ec2 import SecurityGroup, SecurityGroupEgressArgs, SecurityGroupIngressArgs

ecs_elb_security_group = SecurityGroup(
    f"ecs-cluster-{name_prefix}-elb",
    name=f"ecs-cluster-{name_prefix}-elb",
    description=f"ECS cluster {name_prefix} load balancer",
    vpc_id=network.get_output("vpc_id"),
    egress=[
        SecurityGroupEgressArgs(
            description="Allow all outbound traffic by default",
            protocol="-1",
            from_port=0,
            to_port=0,
            cidr_blocks=["0.0.0.0/0"],
        )
    ],
    ingress=[
        SecurityGroupIngressArgs(
            description="Allow HTTP connections from anywhere",
            protocol="tcp",
            from_port=80,
            to_port=80,
            cidr_blocks=["0.0.0.0/0"],
        ),
        SecurityGroupIngressArgs(
            description="Allow HTTPS connections from anywhere",
            protocol="tcp",
            from_port=443,
            to_port=443,
            cidr_blocks=["0.0.0.0/0"],
        )
    ],
    tags={
        "Name": f"ecs-cluster-{name_prefix}-elb",
    }
)

ecs_elb = LoadBalancer(
    name=f'ecs-cluster-{name_prefix}',
    resource_name=f'ecs-cluster-{name_prefix}',
    internal=False,
    load_balancer_type="application",
    subnets=network.get_output("subnets_public"),
    enable_cross_zone_load_balancing=True,
    security_groups=[
        ecs_elb_security_group.id,
    ],
    tags={
        "Name": f'ecs-cluster-{name_prefix}',
    },
)

ecs_elb_listener_http = Listener(
    resource_name=f'ecs-cluster-{name_prefix}-http',
    load_balancer_arn=ecs_elb.arn,
    port=80,
    protocol="HTTP",
    default_actions=[
        ListenerDefaultActionArgs(
            type="fixed-response",
            fixed_response=ListenerDefaultActionFixedResponseArgs(
                content_type="text/plain",
                message_body="Default response",
                status_code="200",
            )
        ),
    ],
)

ecs_elb_target_group_test = TargetGroup(
    resource_name=f'ecs-cluster-{name_prefix}-test',
    name=f'ecs-cluster-{name_prefix}-test',
    port=80,
    protocol="HTTP",
    vpc_id=network.get_output("vpc_id"),
    target_type="ip" if networking_mode == "awsvpc" else "instance",
    tags={
        "Name": f'ecs-cluster-{name_prefix}-test',
    },
)

ecs_elb_listener_rule_test = ListenerRule(
    resource_name=f'ecs-cluster-{name_prefix}-test',
    listener_arn=ecs_elb_listener_http.arn,
    priority=1,
    conditions=[
        ListenerRuleConditionArgs(
            http_header=ListenerRuleConditionHttpHeaderArgs(
                http_header_name="X-test",
                values=["enabled"],
            )
        )
    ],
    actions=[
        ListenerRuleActionArgs(
            order=1,
            type="forward",
            target_group_arn=ecs_elb_target_group_test.arn,
        )
    ]
)
