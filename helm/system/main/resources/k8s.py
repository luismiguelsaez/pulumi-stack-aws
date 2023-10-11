from requests import get
from stack import eks

public_ssh_key = get("https://github.com/luismiguelsaez.keys").text.strip()

userdata_al2_default = f"""
    MIME-Version: 1.0
    Content-Type: multipart/mixed; boundary="BOUNDARY"

    --BOUNDARY
    Content-Type: text/x-shellscript; charset="us-ascii"

    #!/bin/bash
    mkdir /home/ec2-user/.ssh
    chmod 0700 /home/ec2-user/.ssh
    echo "{ public_ssh_key }" >> /home/ec2-user/.ssh/authorized_keys
    chmod 0600 /home/ec2-user/.ssh/authorized_keys
    chown -R ec2-user.ec2-user /home/ec2-user

    --BOUNDARY--
"""

karpenter_awsnodetemplate_al2_default = {
    "apiVersion": "karpenter.k8s.aws/v1alpha1",
    "kind": "AWSNodeTemplate",
    "metadata": {
        "annotations": {},
        "finalizers": [
            "resources-finalizer.argocd.argoproj.io"
        ],
        "name": "al2-default"
    },
    "spec": {
        "amiFamily": "AL2",
        "blockDeviceMappings": [
            {
                "deviceName": "/dev/xvda",
                "ebs": {
                    "encrypted": True,
                    "volumeSize": "20Gi",
                    "volumeType": "gp3"
                }
            }
        ],
        "metadataOptions": {
            "httpEndpoint": "enabled",
            "httpProtocolIPv6": "disabled",
            "httpPutResponseHopLimit": 2,
            "httpTokens": "required"
        },
        "securityGroupSelector": {
            "karpenter.sh/discovery": eks.get_output("eks_cluster_name")
        },
        "subnetSelector": {
            "karpenter.sh/discovery": eks.get_output("eks_cluster_name")
        },
        "userData": userdata_al2_default
    }
}
