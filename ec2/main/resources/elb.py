from stack import network, name_prefix
from pulumi_aws import alb
from resources import ec2

load_balancer = alb.LoadBalancer(
    resource_name=f'{name_prefix}',
    name=f'{name_prefix}',
    load_balancer_type='application',
    security_groups=[ec2.security_group_alb.id],
    subnets=network.get_output('subnets_public'),
)

target_group_default = alb.TargetGroup(
    resource_name=f'{name_prefix}-default',
    name=f'{name_prefix}-default',
    port=80,
    protocol='HTTP',
    target_type='instance',
    vpc_id=network.get_output('vpc_id'),
)

target_group_attachments = []
for instance in range(len(ec2.instances)):
    target_group_attachments.append(
        alb.TargetGroupAttachment(
            resource_name=f'{name_prefix}-{instance}',
            target_group_arn=target_group_default.arn,
            target_id=ec2.instances[instance].id,
            port=80,
        )
    )

load_balancer_listener_http = alb.Listener(
    resource_name=f'{name_prefix}-http',
    load_balancer_arn=load_balancer.arn,
    port=80,
    protocol='HTTP',
    default_actions=[
        alb.ListenerDefaultActionArgs(
            type='forward',
            target_group_arn=target_group_default.arn,
        ),
    ],
)
