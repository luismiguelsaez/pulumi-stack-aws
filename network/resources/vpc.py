from pulumi_aws import ec2, get_availability_zones
import pulumi
import ipaddress

network_config = pulumi.Config("network")
vpc_cidr = network_config.require("cidr")
subnet_mask = network_config.require_int("subnet_mask")

"""
Create VPC
"""
vpc = ec2.Vpc(
    "main",
    cidr_block=vpc_cidr,
    enable_dns_hostnames=True,
    enable_dns_support=True,
    tags={
        "Name": "main",
    },
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
        subnets_public.append(
            ec2.Subnet(
                f"public-{az}",
                assign_ipv6_address_on_creation=False,
                availability_zone=az,
                cidr_block=str(list(ipaddress.IPv4Network(vpc_cidr).subnets(new_prefix=subnet_mask))[i]),
                map_public_ip_on_launch=False,
                tags={
                    "Name": f"public-{az}",
                },
                vpc_id=vpc.id,
            )
        )
    else:
        subnets_private.append(
            ec2.Subnet(
                f"private-{az}",
                assign_ipv6_address_on_creation=False,
                availability_zone=az,
                cidr_block=str(list(ipaddress.IPv4Network(vpc_cidr).subnets(new_prefix=subnet_mask))[i]),
                map_public_ip_on_launch=False,
                tags={
                    "Name": f"private-{az}",
                },
                vpc_id=vpc.id,
            )
        )

"""
Create internet gateway
"""
igw = ec2.InternetGateway(
    "main",
    tags={
        "Name": "main",
    },
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
            f"main-{az}",
            tags={
                "Name": f"main-{az}",
            },
        )
    )

    ngws.append(
        ec2.NatGateway(
            f"main-{az}",
            allocation_id=eips[i].id,
            subnet_id=subnets_public[i].id,
            tags={
                "Name": f"main-{az}",
            },
        )
    )
    
    rts_private.append(
        ec2.RouteTable(
            f"private-{az}",
            tags={
                "Name": f"private-{az}",
            },
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
    "public",
    tags={
        "Name": "public",
    },
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
        f"public-{az}",
        route_table_id=route_table_public.id,
        subnet_id=subnets_public[i].id,
    )

if len(rts_private) > 0:
    for i in range(len(subnets_private)):
        az = azs.names[ i % len(azs.names) ]
        ec2.route_table_association.RouteTableAssociation(
            f"private-{az}",
            route_table_id=rts_private[i].id,
            subnet_id=subnets_private[i].id,
        )
else:
    for i in range(len(subnets_private)):
        az = azs.names[ i % len(azs.names) ]
        ec2.route_table_association.RouteTableAssociation(
            f"private-{az}",
            route_table_id=rts_private[0].id,
            subnet_id=subnets_private[i].id,
        )
