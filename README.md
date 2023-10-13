
```bash
helm registry logout public.ecr.aws

helm upgrade --install karpenter oci://public.ecr.aws/karpenter/karpenter --version v0.31.1 --namespace karpenter --create-namespace \
  --set serviceAccount.annotations."eks\.amazonaws\.com/role-arn"=arn:aws:iam::484308071187:role/karpenter-role \
  --set settings.aws.clusterName=main \
  --set settings.aws.defaultInstanceProfile=karpenter-node-role-instance-profile \
  --set controller.resources.requests.cpu=0.5 \
  --set controller.resources.requests.memory=256Mi \
  --set controller.resources.limits.cpu=0.5 \
  --set controller.resources.limits.memory=256Mi \
  --wait

    #--set settings.aws.interruptionQueueName=main \
```

```bash
cat << EOF | kubectl apply -f -
apiVersion: karpenter.k8s.aws/v1alpha1
kind: AWSNodeTemplate
metadata:
  annotations: {}
  finalizers: []
  name: al2-default
spec:
  amiFamily: AL2
  blockDeviceMappings:
  - deviceName: /dev/xvda
    ebs:
      encrypted: true
      volumeSize: 20Gi
      volumeType: gp3
  metadataOptions:
    httpEndpoint: enabled
    httpProtocolIPv6: disabled
    httpPutResponseHopLimit: 2
    httpTokens: required
  securityGroupSelector:
    karpenter.sh/discovery: main
  subnetSelector:
    karpenter.sh/discovery: main
  userData: |
    MIME-Version: 1.0
    Content-Type: multipart/mixed; boundary="BOUNDARY"

    --BOUNDARY
    Content-Type: text/x-shellscript; charset="us-ascii"

    #!/bin/bash
    mkdir /home/ec2-user/.ssh
    chmod 0700 /home/ec2-user/.ssh
    echo "ssh-rsa ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDD5joG5XuIrFlPXTG83iRQPOJoYE6IrXInZRwW4gX3WCIVW60tJoOmnx4bTytXMpKeWtxPuT9STYD/ehu7YimoOfClTkBZURxs2dK4gdBDYcluD7jkA6SgkGeufu8HLqySnD+myiHNfICgz7proOJU6ggMDqd5Z4zHCjei3IwrY8UU/1s6/9ujHJCUhkRWFT1uKJx79UIwNe2f9IWApBXB9ctQNjc0anwVSWdMfKwcv/w7YSGjR5KF1G/IlCCBGUVyLIftBwIBG/ZBF7VoTDIobnaXStOfFHzFKEzQ6o0AuCk+hFU1sAqhIxU7VOcVYsFrnqRSAx6UBZSY0j00MK+n" >> /home/ec2-user/.ssh/authorized_keys
    chmod 0600 /home/ec2-user/.ssh/authorized_keys
    chown -R ec2-user.ec2-user /home/ec2-user

    --BOUNDARY--
EOF
```
