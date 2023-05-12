#!/usr/bin/env python3
import os

import aws_cdk as cdk

from pipeline import SentimentAnalysisPipelineStack 

app = cdk.App()
SentimentAnalysisPipelineStack(app, "ChatGPTPersonaBotStack",
    env=cdk.Environment(
        account=os.getenv("CDK_DEFAULT_ACCOUNT"),
        region=os.getenv("CDK_DEFAULT_REGION"),
    ),
    
    # Gets the stack name from context.
    stack_name=app.node.try_get_context("stack_name") or "chatgpt-persona-bot",
)

app.synth()