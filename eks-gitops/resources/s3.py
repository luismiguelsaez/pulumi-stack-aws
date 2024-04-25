from pulumi_aws import s3
from pulumi import Output
import pulumi_random as random
from resources.iam_helm import loki_role
from common import common_tags, discovery_tags, stack_config

"""
Create S3 bucket for Loki storage
"""

s3_random_suffix = random.RandomString(
    f"s3-{stack_config.require('name')}-loki-random",
    length=10,
    special=False
)

s3_bucket_loki = s3.Bucket(
    #resource_name=Output.concat(stack_config.require('name'), "-loki-", s3_random_suffix.result),
    resource_name="main-loki-12345678",
    bucket="main-loki-12345678",
    acl="private",
    force_destroy=True,
    policy=Output.json_dumps(
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "AWS": loki_role.arn,
                    },
                    "Action": "s3:*",
                    "Resource": [
                        f"arn:aws:s3:::main-loki-12345678",
                        f"arn:aws:s3:::main-loki-12345678/*",
                    ],
                }
            ]
        }
    ),
    tags={
        "Name": "main-loki-12345678",
    } | common_tags,
)
