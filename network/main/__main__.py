import resources.vpc as vpc
from pulumi import export

export("vpc_id", vpc.vpc.id)
export("subnets_public", [ subnet.id for subnet in vpc.subnets_public ])
export("subnets_private", [ subnet.id for subnet in vpc.subnets_private ])
export("availability_zones", vpc.azs.names)
