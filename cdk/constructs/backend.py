from aws_cdk import (
    aws_secretsmanager,
    aws_ecs,
    aws_ecs_patterns,
    aws_ec2,
    aws_ssm
)
from constructs import Construct

class Backend(Construct):
    def __init__(self, scope: Construct, id: str):
        super().__init__(scope, id)

        vpc_id = aws_ssm.StringParameter.value_from_lookup(scope, parameter_name="/baseline/infra/v2/vpc/id")
        vpc = aws_ec2.Vpc.from_lookup(self, id="BaselineVPC", vpc_id=vpc_id)

        cluster_name = aws_ssm.StringParameter.value_from_lookup(scope, parameter_name="/baseline/infra/v2/ecs/cluster/name")
        cluster = aws_ecs.Cluster.from_cluster_attributes(self, id="BaselineCluster", cluster_name=cluster_name, vpc=vpc)

        scalegrid_secret = aws_secretsmanager.Secret(self, "scalegridDB")
        modal_secret = aws_secretsmanager.Secret(self, "modalConfig")
        auth0_config = aws_secretsmanager.Secret(self, "auth0Config")

        task_options = aws_ecs_patterns.ApplicationLoadBalancedTaskImageOptions(image=aws_ecs.ContainerImage.from_asset("."), container_port=8888)
        service = aws_ecs_patterns.ApplicationLoadBalancedFargateService(self, "BackendApi", assign_public_ip=True, desired_count=2, cluster=cluster, task_image_options=task_options)