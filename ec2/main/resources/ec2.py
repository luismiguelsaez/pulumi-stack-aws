from stack import network, ec2_config, name_prefix
from pulumi_aws import ec2, get_availability_zones
from requests import get

# Get AMI based on OS filter
ami = ec2.get_ami(
    most_recent=True,
    owners=['amazon'],
    filters=[
        ec2.GetAmiFilterArgs(
            name='name',
            values=['amzn2-ami-hvm-*-x86_64-ebs'],
        ),
    ],
)

public_ssh_key = get("https://github.com/luismiguelsaez.keys").text.strip()

key_pair = ec2.KeyPair(
    f'{name_prefix}',
    key_name=f'{name_prefix}',
    public_key=public_ssh_key,
)

security_group = ec2.SecurityGroup(
    resource_name=f'{name_prefix}',
    description=f'{name_prefix}',
    vpc_id=network.get_output('vpc_id'),
    ingress=[
        ec2.SecurityGroupIngressArgs(
            protocol='tcp',
            from_port=22,
            to_port=22,
            cidr_blocks=['0.0.0.0/0'],
        ),
    ],
    egress=[
        ec2.SecurityGroupEgressArgs(
            protocol='-1',
            from_port=0,
            to_port=0,
            cidr_blocks=['0.0.0.0/0'],
        ),
    ],
)

instances = []

for instance in range(ec2_config.require_int('instance_count')):
    instances.append(
        ec2.Instance(
            f'{name_prefix}-{instance}',
            instance_type=ec2_config.require('instance_size'),
            ami=ami.id,
            subnet_id=network.get_output('subnets_public')[instance],
            associate_public_ip_address=True,
            security_groups=[security_group.id],
            key_name=key_pair.key_name,
            tags={
                'Name': f'{name_prefix}-{instance}',
            },
        )
    )
