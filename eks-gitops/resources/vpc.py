from pulumi import Config, get_project, get_stack
from pulumi_aws import ec2, get_availability_zones
import ipaddress
from common import stack_config, vpc_config, common_tags, discovery_tags_public, discovery_tags_private

"""
Create VPC
"""
vpc = ec2.Vpc(
    f"{stack_config.require('name')}",
    cidr_block=vpc_config.require("cidr"),
    enable_dns_hostnames=True,
    enable_dns_support=True,
    tags={
        "Name": f"{stack_config.require('name')}",
    } | common_tags,
)

"""
Get availability zones
"""
azs = get_availability_zones(state="available")

"""
Create subnets
"""
subnets_public = []
subnets_private = []

for i in range(vpc_config.require_int("azs") * 2):
    az = azs.names[ i % len(azs.names) ]
    if i % 2 == 0:
        tags = {"Name": f"{stack_config.require('name')}-public-{az}"}
        subnets_public.append(
            ec2.Subnet(
                f"{stack_config.require('name')}-public-{az}",
                assign_ipv6_address_on_creation=False,
                availability_zone=az,
                cidr_block=str(list(ipaddress.IPv4Network(vpc_config.require("cidr")).subnets(new_prefix=vpc_config.require_int("subnet_mask")))[i]),
                map_public_ip_on_launch=False,
                tags=tags | common_tags | discovery_tags_public,
                vpc_id=vpc.id,
            )
        )
    else:
        tags = {"Name": f"{stack_config.require('name')}-private-{az}"}
        subnets_private.append(
            ec2.Subnet(
                f"{stack_config.require('name')}-private-{az}",
                assign_ipv6_address_on_creation=False,
                availability_zone=az,
                cidr_block=str(list(ipaddress.IPv4Network(vpc_config.require("cidr")).subnets(new_prefix=vpc_config.require_int("subnet_mask")))[i]),
                map_public_ip_on_launch=False,
                tags=tags | common_tags | discovery_tags_private,
                vpc_id=vpc.id,
            )
        )

"""
Create internet gateway
"""
igw = ec2.InternetGateway(
    f"{stack_config.require('name')}",
    tags={
        "Name": f"{stack_config.require('name')}",
    } | common_tags,
    vpc_id=vpc.id,
)

"""
Create NAT gateway
"""
eips = []
ngws = []
rts_private = []

if vpc_config.require_bool("ngw_multi_az"):
    ngw_count = vpc_config.require_int("azs")
else:
    ngw_count = 1

for i in range(ngw_count):
    az = azs.names[ i % len(azs.names) ]
    
    eips.append(
        ec2.Eip(
            f"{stack_config.require('name')}-{az}",
            tags={
                "Name": f"{stack_config.require('name')}-{az}",
            } | common_tags,
        )
    )

    ngws.append(
        ec2.NatGateway(
            f"{stack_config.require('name')}-{az}",
            allocation_id=eips[i].id,
            subnet_id=subnets_public[i].id,
            tags={
                "Name": f"{stack_config.require('name')}-{az}",
            } | common_tags,
        )
    )
    
    rts_private.append(
        ec2.RouteTable(
            f"{stack_config.require('name')}-private-{az}",
            tags={
                "Name": f"{stack_config.require('name')}-private-{az}",
            } | common_tags,
            vpc_id=vpc.id,
            routes=[
                ec2.RouteTableRouteArgs(
                    cidr_block="0.0.0.0/0",
                    nat_gateway_id=ngws[i].id,
                )
            ],
        )
    )


"""
Create route tables
"""
route_table_public = ec2.RouteTable(
    f"{stack_config.require('name')}-public",
    tags={
        "Name": f"{stack_config.require('name')}-public",
    } | common_tags,
    vpc_id=vpc.id,
    routes=[
        ec2.RouteTableRouteArgs(
            cidr_block="0.0.0.0/0",
            gateway_id=igw.id,
        )
    ],
)

"""
Create route table associations
"""
for i in range(len(subnets_public)):
    az = azs.names[ i % len(azs.names) ]
    ec2.route_table_association.RouteTableAssociation(
        f"{stack_config.require('name')}-public-{az}",
        route_table_id=route_table_public.id,
        subnet_id=subnets_public[i].id,
    )

if len(rts_private) > 1:
    for i in range(len(subnets_private)):
        az = azs.names[ i % len(azs.names) ]
        ec2.route_table_association.RouteTableAssociation(
            f"{stack_config.require('name')}-private-{az}",
            route_table_id=rts_private[i].id,
            subnet_id=subnets_private[i].id,
        )
else:
    for i in range(len(subnets_private)):
        az = azs.names[ i % len(azs.names) ]
        ec2.route_table_association.RouteTableAssociation(
            f"{stack_config.require('name')}-private-{az}",
            route_table_id=rts_private[0].id,
            subnet_id=subnets_private[i].id,
        )
