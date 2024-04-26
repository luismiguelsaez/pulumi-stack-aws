from pulumi_aws import s3
from pulumi import Output
import pulumi_random as random
from resources.iam_helm import loki_role
from common import env, common_tags, stack_config

"""
Create S3 bucket for Loki storage
"""

s3_random_suffix = random.RandomString(
    f"s3-{stack_config.require('name')}-loki-random",
    length=10,
    lower=True,
    upper=False,
    special=False
)

s3_bucket_loki = s3.Bucket(
    resource_name="main-loki-12345678",
    bucket=Output.concat(env, "-", stack_config.require('name'), "-loki-", s3_random_suffix.result),
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
                        Output.concat("arn:aws:s3:::", env, "-", stack_config.require('name'), "-loki-", s3_random_suffix.result),
                        Output.concat("arn:aws:s3:::", env, "-", stack_config.require('name'), "-loki-", s3_random_suffix.result, "/*")
                    ],
                }
            ]
        }
    ),
    tags={
        "Name": Output.concat(env, "-", stack_config.require('name'), "-loki-", s3_random_suffix.result),
    } | common_tags,
)
