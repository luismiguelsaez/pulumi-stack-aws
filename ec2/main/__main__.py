from resources import ec2, elb
from pulumi import export

export('instance_public_ips', [instance.public_ip for instance in ec2.instances])
