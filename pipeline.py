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

        ########################################################
        # A DynamoDB table
        ########################################################

        # Create a DynamoDB table
        personas_table = aws_dynamodb.Table(
            self,
            f"{self.stack_name}-personas",
            table_name=f"{self.stack_name}-personas",
            partition_key=aws_dynamodb.Attribute(
                name="name",
                type=aws_dynamodb.AttributeType.STRING
            ),
            billing_mode=aws_dynamodb.BillingMode.PAY_PER_REQUEST,
        )

        ########################################################
        # SQS Queue
        ########################################################

        # Create an SQS queue to hold the messages.
        queue = aws_sqs.Queue(
            self,
            f"{self.stack_name}-queue",
            queue_name=f"{self.stack_name}-queue",
            visibility_timeout=Duration.seconds(300)
        )

        ########################################################
        # Parameter Store
        ########################################################

        # Create a Parameter Store parameter to hold 
        # the Slack bot token and OpenAI API key.
        
        ssm_slack_token = aws_ssm.StringParameter(
            self,
            f"{self.stack_name}-slack-token",
            parameter_name=f"{self.stack_name}-slack-token",
            string_value="CHANGE_ME",
        )

        ssm_openai_key = aws_ssm.StringParameter(
            self,
            f"{self.stack_name}-openai-api-key",
            parameter_name=f"{self.stack_name}-openai-api-key",
            string_value="CHANGE_ME",
        )

        ########################################################
        # Lambda Layer
        ########################################################

        openai_layer = aws_lambda_python_alpha.PythonLayerVersion(
            self,
            f"{self.stack_name}-openai-layer",
            entry="layers/openai",
            layer_version_name=f"{self.stack_name}-openai-layer",
            compatible_runtimes=[aws_lambda.Runtime.PYTHON_3_8],
        )

        ########################################################
        # A Lambda function
        ########################################################

        # Create a Lambda function
        # A Lambda function that will validate the file uploaded to the S3 bucket.
        create_persona_fn = aws_lambda_python_alpha.PythonFunction(
            self,
            f"{self.stack_name}-create-persona",
            function_name=f"{self.stack_name}-create-persona",
            runtime=aws_lambda.Runtime.PYTHON_3_8,
            index="main.py",
            handler="handler",
            entry="lambdas/create_persona",
            environment={
                "TABLE_NAME": personas_table.table_name
            }
        )

        delete_persona_fn = aws_lambda_python_alpha.PythonFunction(
            self,
            f"{self.stack_name}-delete-persona",
            function_name=f"{self.stack_name}-delete-persona",
            runtime=aws_lambda.Runtime.PYTHON_3_8,
            index="main.py",
            handler="handler",
            entry="lambdas/delete_persona",
            environment={
                "TABLE_NAME": personas_table.table_name
            }
        )

        get_personas_fn = aws_lambda_python_alpha.PythonFunction(
            self,
            f"{self.stack_name}-get-personas",
            function_name=f"{self.stack_name}-get-personas",
            runtime=aws_lambda.Runtime.PYTHON_3_8,
            index="main.py",
            handler="handler",
            entry="lambdas/get_personas",
            environment={
                "TABLE_NAME": personas_table.table_name
            }
        )

        ask_persona_fn = aws_lambda_python_alpha.PythonFunction(
            self,
            f"{self.stack_name}-ask-persona",
            function_name=f"{self.stack_name}-ask-persona",
            runtime=aws_lambda.Runtime.PYTHON_3_8,
            index="main.py",
            handler="handler",
            entry="lambdas/ask_persona",
            environment={
                "TABLE_NAME": personas_table.table_name,
                "SSM_SLACK_TOKEN": ssm_slack_token.parameter_name,
            },
            layers=[openai_layer]
        )

        slack_fn = aws_lambda_python_alpha.PythonFunction(
            self,
            f"{self.stack_name}-slack-queue",
            function_name=f"{self.stack_name}-slack-queue",
            runtime=aws_lambda.Runtime.PYTHON_3_8,
            index="main.py",
            handler="handler",
            entry="lambdas/slack_queue",
            environment={
                "SQS_QUEUE_URL": queue.queue_url
            }
        )

        slack_respond_fn = aws_lambda_python_alpha.PythonFunction(
            self,
            f"{self.stack_name}-slack-respond",
            function_name=f"{self.stack_name}-slack-respond",
            runtime=aws_lambda.Runtime.PYTHON_3_8,
            index="main.py",
            handler="handler",
            entry="lambdas/slack_respond",
            environment={
                "TABLE_NAME": personas_table.table_name,
                "SSM_OPENAI_API_KEY": ssm_openai_key.parameter_name,
                "SSM_SLACK_TOKEN": ssm_slack_token.parameter_name,
                "MAX_OPENAI_TOKENS": "150"
            },
            layers=[openai_layer],
            timeout=Duration.seconds(300)
        )

        ########################################################
        # Lambda Permissions
        ########################################################

        # Give the Lambda function permissions to read and write to the DynamoDB table
        personas_table.grant_read_write_data(create_persona_fn)
        personas_table.grant_read_write_data(delete_persona_fn)
        personas_table.grant_read_data(get_personas_fn)
        personas_table.grant_read_data(ask_persona_fn)
        personas_table.grant_read_data(slack_respond_fn)

        # Give the Lambda function permissions to read from the SQS queue
        queue.grant_send_messages(slack_fn)

        # Give the Lambda function permissions to read from SSM
        ssm_slack_token.grant_read(slack_respond_fn)
        ssm_openai_key.grant_read(ask_persona_fn)
        ssm_openai_key.grant_read(slack_respond_fn)

        ########################################################
        # SQS Trigger
        ########################################################

        # Create an SQS trigger for the Lambda function
        slack_respond_fn.add_event_source(
            aws_lambda_event_sources.SqsEventSource(
                queue=queue,
                batch_size=1
            )
        )

        ########################################################
        # An HTTP API integration
        ########################################################

        # Add a new route to the HTTP API
        create_persona_integration = HttpLambdaIntegration(
            f"{self.stack_name}-create-persona-integration",
            create_persona_fn
        )

        delete_persona_integration = HttpLambdaIntegration(
            f"{self.stack_name}-delete-persona-integration",
            delete_persona_fn
        )

        get_personas_integration = HttpLambdaIntegration(
            f"{self.stack_name}-get-personas-integration",
            get_personas_fn
        )

        ask_persona_integration = HttpLambdaIntegration(
            f"{self.stack_name}-ask-persona-integration",
            ask_persona_fn
        )

        slack_integration = HttpLambdaIntegration(
            f"{self.stack_name}-slack-integration",
            slack_fn
        )
                                              
        ########################################################
        # An HTTP API
        ########################################################

        # An HTTP API
        http_api = aws_apigwv2.HttpApi(self, "AIHttpAPI",
            api_name="ai-http-api",
        )

        http_api.add_routes(
            path="/persona",
            methods=[aws_apigwv2.HttpMethod.POST],
            integration=create_persona_integration
        )

        http_api.add_routes(
            path="/persona",
            methods=[aws_apigwv2.HttpMethod.DELETE],
            integration=delete_persona_integration
        )

        http_api.add_routes(
            path="/personas",
            methods=[aws_apigwv2.HttpMethod.GET],
            integration=get_personas_integration
        )

        http_api.add_routes(
            path="/persona/ask",
            methods=[aws_apigwv2.HttpMethod.POST],
            integration=ask_persona_integration
        )

        http_api.add_routes(
            path="/slack/{persona}",
            methods=[aws_apigwv2.HttpMethod.POST],
            integration=slack_integration
        )

