from aws_cdk import (
    Stack,
    Duration,
    aws_apigatewayv2_alpha as aws_apigwv2,
    aws_dynamodb,
    aws_lambda,
    aws_lambda_event_sources,
    aws_lambda_python_alpha,
    aws_sqs,
    aws_ssm
)
from constructs import Construct
from aws_cdk.aws_apigatewayv2_integrations_alpha import HttpLambdaIntegration

class SentimentAnalysisPipelineStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        ##############################
        # Your code goes here
        ##############################