from resources import ecs, elb
from pulumi import export

export('alb_dns_name', elb.ecs_elb.dns_name)
export('alb_listener_http_port', elb.ecs_elb_listener_http.port)
