from os import name
from pulumi_aws import ec2, get_availability_zones
import pulumi
import ipaddress
from .tags import common_tags
from stack import network_config

vpc_cidr = network_config.require("cidr")
subnet_mask = network_config.require_int("subnet_mask")
name_prefix = network_config.require("name_prefix")

discovery_tags = {
    "karpenter.sh/discovery": name_prefix,
}

"""
Create VPC
"""
vpc = ec2.Vpc(
    f"{name_prefix}",
    cidr_block=vpc_cidr,
    enable_dns_hostnames=True,
    enable_dns_support=True,
    tags={
        "Name": f"{name_prefix}",
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

for i in range(network_config.require_int("azs") * 2):
    az = azs.names[ i % len(azs.names) ]
    if i % 2 == 0:
        tags = {"Name": f"{name_prefix}-public-{az}"}
        subnets_public.append(
            ec2.Subnet(
                f"{name_prefix}-public-{az}",
                assign_ipv6_address_on_creation=False,
                availability_zone=az,
                cidr_block=str(list(ipaddress.IPv4Network(vpc_cidr).subnets(new_prefix=subnet_mask))[i]),
                map_public_ip_on_launch=False,
                tags=tags | common_tags | discovery_tags,
                vpc_id=vpc.id,
            )
        )
    else:
        tags = {"Name": f"{name_prefix}-private-{az}"}
        subnets_private.append(
            ec2.Subnet(
                f"{name_prefix}-private-{az}",
                assign_ipv6_address_on_creation=False,
                availability_zone=az,
                cidr_block=str(list(ipaddress.IPv4Network(vpc_cidr).subnets(new_prefix=subnet_mask))[i]),
                map_public_ip_on_launch=False,
                tags=tags | common_tags | discovery_tags,
                vpc_id=vpc.id,
            )
        )

"""
Create internet gateway
"""
igw = ec2.InternetGateway(
    f"{name_prefix}",
    tags={
        "Name": f"{name_prefix}",
    } | common_tags,
    vpc_id=vpc.id,
)

"""
Create NAT gateway
"""
eips = []
ngws = []
rts_private = []

if network_config.require_bool("ngw_multi_az"):
    ngw_count = network_config.require_int("azs")
else:
    ngw_count = 1

for i in range(ngw_count):
    az = azs.names[ i % len(azs.names) ]
    
    eips.append(
        ec2.Eip(
            f"{name_prefix}-{az}",
            tags={
                "Name": f"{name_prefix}-{az}",
            } | common_tags,
        )
    )

    ngws.append(
        ec2.NatGateway(
            f"{name_prefix}-{az}",
            allocation_id=eips[i].id,
            subnet_id=subnets_public[i].id,
            tags={
                "Name": f"{name_prefix}-{az}",
            } | common_tags,
        )
    )
    
    rts_private.append(
        ec2.RouteTable(
            f"{name_prefix}-private-{az}",
            tags={
                "Name": f"{name_prefix}-private-{az}",
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
    f"{name_prefix}-public",
    tags={
        "Name": f"{name_prefix}-public",
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
        f"{name_prefix}-public-{az}",
        route_table_id=route_table_public.id,
        subnet_id=subnets_public[i].id,
    )

if len(rts_private) > 1:
    for i in range(len(subnets_private)):
        az = azs.names[ i % len(azs.names) ]
        ec2.route_table_association.RouteTableAssociation(
            f"{name_prefix}-private-{az}",
            route_table_id=rts_private[i].id,
            subnet_id=subnets_private[i].id,
        )
else:
    for i in range(len(subnets_private)):
        az = azs.names[ i % len(azs.names) ]
        ec2.route_table_association.RouteTableAssociation(
            f"{name_prefix}-private-{az}",
            route_table_id=rts_private[0].id,
            subnet_id=subnets_private[i].id,
        )
